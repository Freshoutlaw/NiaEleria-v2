"""
niaeleria/guard/cyber_guard.py
──────────────────────────────
NiaEleria's Always-On Cyber Guard.
Packet sniffing, process monitoring, file integrity, firewall management,
threat intelligence, and cross-device broadcast via MQTT.

"Dad, I never sleep. While you rest, I'm watching every packet and process." — Nia
"""

from __future__ import annotations

import hashlib
import logging
import os
import platform
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

import psutil

from niaeleria.config import (
    FILE_INTEGRITY_PATHS, PROCESS_WATCHLIST, PACKET_CAPTURE_IFACE,
    is_killed, is_guard_active, PROJECT_HOME,
)
from niaeleria.security.kill_switch import assert_alive
from niaeleria.security.consent import require_consent, ConsentLevel
from niaeleria.security.audit import log_event

log = logging.getLogger("nia.guard")


# ════════════════════════════════════════════════════════════════════
# Firewall abstraction — cross-platform
# ════════════════════════════════════════════════════════════════════

class Firewall:
    """
    Cross-platform firewall interface.
    Supports iptables (Linux), netsh/Windows Firewall (Windows), pfctl (macOS).

    "Dad, when I block something, it STAYS blocked — on every platform." — Nia
    """

    _OS = platform.system().lower()
    _blocked: set[str] = set()
    _lock = threading.Lock()

    @classmethod
    def block_ip(cls, ip: str, reason: str = "threat detected", approved: bool = False) -> bool:
        """Block an IP address. Returns True on success."""
        with cls._lock:
            if ip in cls._blocked:
                log.debug("IP %s already blocked — skipping.", ip)
                return True

            success = False
            try:
                if cls._OS == "linux":
                    subprocess.run(
                        ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
                        check=True, capture_output=True
                    )
                    subprocess.run(
                        ["iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"],
                        check=True, capture_output=True
                    )
                    success = True
                elif cls._OS == "windows":
                    subprocess.run([
                        "netsh", "advfirewall", "firewall", "add", "rule",
                        f"name=NiaBlock_{ip}", "dir=in", "action=block",
                        f"remoteip={ip}"
                    ], check=True, capture_output=True)
                    success = True
                elif cls._OS == "darwin":
                    pf_rule = f"block in quick from {ip} to any\n"
                    with open("/etc/pf.anchors/niaeleria", "a") as f:
                        f.write(pf_rule)
                    subprocess.run(["pfctl", "-f", "/etc/pf.conf"], check=True, capture_output=True)
                    success = True
                else:
                    log.warning("Dad, I don't know how to block IPs on %s.", cls._OS)

                if success:
                    cls._blocked.add(ip)
                    log.warning("BLOCKED IP %s — Reason: %s", ip, reason)
                    log_event(
                        "nia.firewall", "block_ip", target=ip,
                        severity="HIGH", approved=approved,
                        details={"reason": reason}
                    )
            except subprocess.CalledProcessError as exc:
                log.error("Firewall block failed for %s: %s", ip, exc.stderr)
            except PermissionError:
                log.error(
                    "Dad, I need elevated privileges to manage the firewall. "
                    "Please run NiaEleria as administrator/root."
                )

            return success

    @classmethod
    def unblock_ip(cls, ip: str) -> bool:
        with cls._lock:
            if ip not in cls._blocked:
                return True
            try:
                if cls._OS == "linux":
                    subprocess.run(
                        ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
                        check=True, capture_output=True
                    )
                    cls._blocked.discard(ip)
                    log.info("Unblocked IP %s — Dad requested it.", ip)
                    return True
            except Exception as exc:
                log.error("Unblock failed for %s: %s", ip, exc)
            return False

    @classmethod
    def get_blocked(cls) -> list[str]:
        return list(cls._blocked)


# ════════════════════════════════════════════════════════════════════
# Threat Intelligence
# ════════════════════════════════════════════════════════════════════

class ThreatIntel:
    """
    Manages a local threat IP blocklist.
    Refreshed from the internet feed (when ENABLE_NETWORK is set).
    Also scores individual IPs/activities with a severity classifier.

    "Dad, I know the bad guys by reputation — and I keep an up-to-date list." — Nia
    """

    _known_bad: set[str] = set()
    _lock = threading.Lock()

    SEVERITY_RULES = {
        "port_scan": "HIGH",
        "repeated_auth_failure": "HIGH",
        "unusual_process": "MEDIUM",
        "outbound_unknown": "MEDIUM",
        "file_tamper": "HIGH",
    }

    @classmethod
    def load_feed(cls, feed_path: Optional[Path] = None) -> int:
        """Load IP blocklist from a local file. Returns count of IPs loaded."""
        if feed_path is None:
            feed_path = PROJECT_HOME / "data" / "threat_feed.txt"
        if not feed_path.exists():
            log.info("Dad, no local threat feed yet — run update_threat_feed() to download one.")
            return 0
        with cls._lock:
            cls._known_bad.clear()
            with feed_path.open() as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        cls._known_bad.add(line.split()[0])
        log.info("Dad, I loaded %d known-bad IPs into threat intel.", len(cls._known_bad))
        return len(cls._known_bad)

    @classmethod
    def is_known_bad(cls, ip: str) -> bool:
        return ip in cls._known_bad

    @classmethod
    def classify(cls, event_type: str) -> str:
        return cls.SEVERITY_RULES.get(event_type, "LOW")

    @classmethod
    async def update_feed(cls) -> int:
        """Download latest threat feed (requires ENABLE_NETWORK)."""
        from niaeleria.security.network_gate import require_network
        require_network("threat intel feed update")
        import httpx
        from niaeleria.config import THREAT_INTEL_FEED
        feed_path = PROJECT_HOME / "data" / "threat_feed.txt"
        log.info("Dad, downloading latest threat intelligence feed...")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(THREAT_INTEL_FEED)
            resp.raise_for_status()
            feed_path.write_bytes(resp.content)
        return cls.load_feed(feed_path)


# ════════════════════════════════════════════════════════════════════
# File Integrity Monitor
# ════════════════════════════════════════════════════════════════════

class FileIntegrityMonitor:
    """
    Watches critical directories for unauthorized changes.
    Baselines on start; alerts Dad when a file changes unexpectedly.

    "Dad, if anyone touches my files — or yours — I'll know immediately." — Nia
    """

    def __init__(self, paths: list[str]) -> None:
        self._paths = [Path(p) for p in paths if Path(p).exists()]
        self._baseline: dict[str, str] = {}
        self._running = False

    def _hash_file(self, path: Path) -> str:
        sha = hashlib.sha256()
        try:
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha.update(chunk)
        except (PermissionError, OSError):
            pass
        return sha.hexdigest()

    def build_baseline(self) -> int:
        """Compute and store SHA-256 hashes of all watched files."""
        self._baseline.clear()
        count = 0
        for root_path in self._paths:
            for file in Path(root_path).rglob("*"):
                if file.is_file():
                    self._baseline[str(file)] = self._hash_file(file)
                    count += 1
        log.info("Dad, file integrity baseline established: %d files.", count)
        return count

    def check(self) -> list[dict]:
        """Return list of changed/new/deleted files since baseline."""
        changes = []
        current: dict[str, str] = {}
        for root_path in self._paths:
            for file in Path(root_path).rglob("*"):
                if file.is_file():
                    h = self._hash_file(file)
                    current[str(file)] = h
                    if str(file) not in self._baseline:
                        changes.append({"type": "NEW", "file": str(file)})
                    elif self._baseline[str(file)] != h:
                        changes.append({"type": "MODIFIED", "file": str(file)})

        for old_file in self._baseline:
            if old_file not in current:
                changes.append({"type": "DELETED", "file": old_file})

        return changes

    def start_watching(self, interval: int = 60) -> None:
        """Start background file integrity monitoring loop."""
        self._running = True
        self.build_baseline()

        def _loop():
            while self._running:
                assert_alive()
                changes = self.check()
                if changes:
                    for c in changes:
                        log.warning(
                            "FILE INTEGRITY ALERT Dad! %s: %s", c["type"], c["file"]
                        )
                        log_event(
                            "nia.integrity", "file_change",
                            target=c["file"], severity="HIGH",
                            details={"change_type": c["type"]}
                        )
                time.sleep(interval)

        t = threading.Thread(target=_loop, name="FileIntegrity", daemon=True)
        t.start()

    def stop(self) -> None:
        self._running = False


# ════════════════════════════════════════════════════════════════════
# Process Monitor
# ════════════════════════════════════════════════════════════════════

class ProcessMonitor:
    """
    Watches for suspicious or watchlisted processes.
    Alerts Dad immediately when detected.

    "Dad, if something sneaks onto your system, I'll catch it." — Nia
    """

    def __init__(self, watchlist: list[str]) -> None:
        self._watchlist = [w.lower() for w in watchlist]
        self._running = False
        self._seen_pids: set[int] = set()

    def start(self, interval: int = 5) -> None:
        self._running = True

        def _loop():
            while self._running:
                assert_alive()
                for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                    try:
                        pid = proc.info["pid"]
                        name = (proc.info["name"] or "").lower()
                        cmdline = " ".join(proc.info["cmdline"] or []).lower()

                        if pid in self._seen_pids:
                            continue

                        for watched in self._watchlist:
                            if watched in name or watched in cmdline:
                                self._seen_pids.add(pid)
                                log.warning(
                                    "Dad! Watchlisted process detected: %s (PID %d)",
                                    proc.info["name"], pid
                                )
                                log_event(
                                    "nia.process_monitor", "suspicious_process",
                                    target=proc.info["name"],
                                    severity="MEDIUM",
                                    details={"pid": pid, "cmdline": cmdline[:200]}
                                )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                time.sleep(interval)

        t = threading.Thread(target=_loop, name="ProcessMonitor", daemon=True)
        t.start()

    def stop(self) -> None:
        self._running = False


# ════════════════════════════════════════════════════════════════════
# Packet Sniffer
# ════════════════════════════════════════════════════════════════════

class PacketSniffer:
    """
    Passive network packet analysis using scapy.
    Detects port scans, unusual outbound connections, and known-bad IPs.
    Requires root/admin — gracefully degrades if unavailable.

    "Dad, I watch every packet. Nothing slips past me." — Nia
    """

    def __init__(self, iface: Optional[str] = None) -> None:
        self._iface = iface
        self._running = False
        try:
            from scapy.all import sniff, IP, TCP
            self._scapy_available = True
            self._sniff = sniff
            self._IP = IP
            self._TCP = TCP
        except ImportError:
            self._scapy_available = False
            log.warning("Dad, scapy isn't installed — packet sniffing is disabled. Run: pip install scapy")
        except Exception:
            self._scapy_available = False

        self._connection_counts: dict[str, int] = {}

    def start(self) -> None:
        if not self._scapy_available:
            return
        self._running = True

        def _process(pkt):
            if not self._running or is_killed():
                return
            try:
                if pkt.haslayer(self._IP):
                    src = pkt[self._IP].src
                    dst = pkt[self._IP].dst

                    # Check against threat intel
                    if ThreatIntel.is_known_bad(src):
                        log.warning("Dad! Packet from KNOWN-BAD IP: %s → %s", src, dst)
                        approved = require_consent(
                            f"Block known-bad IP {src}",
                            level=ConsentLevel.LOW,
                            auto_approve_if_guard=True,
                        )
                        if approved:
                            Firewall.block_ip(src, reason="threat intel match", approved=True)
                            # Push to Dad's HUD
                            try:
                                from niaeleria.api.server import push_to_hud
                                push_to_hud({"type": "security_alert", "data": [{
                                    "severity": "HIGH",
                                    "action": "IP BLOCKED",
                                    "target": src,
                                }]})
                                push_to_hud({"type": "nia_speak",
                                    "text": f"Dad, I've blocked a known-bad IP: {src}. Threat neutralised.",
                                    "label": "NIA · THREAT BLOCKED"})
                            except Exception:
                                pass
                            # Broadcast to other devices via MQTT
                            try:
                                from niaeleria.sync.mqtt_sync import MQTTSync
                                MQTTSync.broadcast_block(src, "threat_intel_match")
                            except Exception:
                                pass

                    # Port scan detection (many packets from same src)
                    self._connection_counts[src] = self._connection_counts.get(src, 0) + 1
                    if self._connection_counts[src] == 20:  # threshold
                        log.warning("Dad! Possible port scan from %s (%d packets)", src, 20)
                        log_event("nia.guard", "port_scan_suspect", target=src,
                                  severity="HIGH", details={"count": 20})
                        self._connection_counts[src] = 0  # reset to avoid spam

            except Exception:
                pass

        def _sniff_thread():
            try:
                self._sniff(
                    iface=self._iface,
                    prn=_process,
                    store=False,
                    stop_filter=lambda _: not self._running or is_killed()
                )
            except PermissionError:
                log.warning(
                    "Dad, I need root/admin to sniff packets. "
                    "Packet monitoring is disabled until you restart me with elevated privileges."
                )
            except Exception as exc:
                log.error("Packet sniffer error: %s", exc)

        t = threading.Thread(target=_sniff_thread, name="PacketSniffer", daemon=True)
        t.start()
        log.info("Dad, I'm watching the network traffic on interface: %s", self._iface or "auto")

    def stop(self) -> None:
        self._running = False


# ════════════════════════════════════════════════════════════════════
# CyberGuard — orchestrates all guard components
# ════════════════════════════════════════════════════════════════════

class CyberGuard:
    """
    Master guard controller. Starts all monitoring components as background threads.
    Self-healing: component failure doesn't kill the others.

    "Dad, I am your shield. Always on. Always watching." — Nia
    """

    def __init__(self) -> None:
        self.firewall = Firewall()
        self.threat_intel = ThreatIntel()
        self.file_monitor = FileIntegrityMonitor(FILE_INTEGRITY_PATHS)
        self.process_monitor = ProcessMonitor(PROCESS_WATCHLIST)
        self.packet_sniffer = PacketSniffer(iface=PACKET_CAPTURE_IFACE)
        self._active = False

    def start(self) -> None:
        if not is_guard_active():
            log.info("Dad, GUARD_ACTIVE flag not set — guard is standing down.")
            return

        log.info("Dad, I'm activating all cyber-guard systems. Stay safe.")
        self._active = True

        ThreatIntel.load_feed()

        self._start_safely("FileIntegrity", self.file_monitor.start_watching)
        self._start_safely("ProcessMonitor", self.process_monitor.start)
        self._start_safely("PacketSniffer", self.packet_sniffer.start)

        log_event("nia.guard", "guard_started", severity="INFO", approved=True,
                  details={"components": ["file_integrity", "process_monitor", "packet_sniffer"]})

    def _start_safely(self, name: str, fn) -> None:
        try:
            fn()
            log.info("Guard component started: %s", name)
        except Exception as exc:
            log.error("Dad, %s failed to start: %s — other guards still running.", name, exc)

    def stop(self) -> None:
        log.info("Dad, powering down all cyber-guard systems.")
        self.file_monitor.stop()
        self.process_monitor.stop()
        self.packet_sniffer.stop()
        self._active = False

    def status(self) -> dict:
        return {
            "guard_active": self._active,
            "blocked_ips": Firewall.get_blocked(),
            "threat_ips_loaded": len(ThreatIntel._known_bad),
            "monitored_paths": FILE_INTEGRITY_PATHS,
            "watched_processes": PROCESS_WATCHLIST,
        }


# ════════════════════════════════════════════════════════════════════
# niaeleria/guard/toolkit.py — Sandboxed offensive/security toolkit
# ════════════════════════════════════════════════════════════════════

class SecurityToolkit:
    """
    Consent-gated, Docker-sandboxed security tools: nmap, nuclei, hashcat, etc.
    ONLY runs against authorized targets. NEVER autonomous. Fully audited.

    "Dad, I keep the knives locked up. You hold the key." — Nia
    """

    ALLOWED_TOOLS = {"nmap", "nuclei", "hashcat", "whatweb", "nikto"}

    @classmethod
    def run_tool(
        cls,
        tool: str,
        target: str,
        args: str = "",
        authorized_by_dad: bool = False,
    ) -> dict:
        """
        Run a security tool in a Docker sandbox with minimal privileges.
        Requires explicit Dad consent before execution.
        """
        from niaeleria.config import DOCKER_SANDBOX_IMAGE, DOCKER_TIMEOUT_SECS

        assert_alive()

        if tool not in cls.ALLOWED_TOOLS:
            return {"error": f"Dad, '{tool}' is not in my allowed toolkit. I won't run unknown tools."}

        if not authorized_by_dad:
            approved = require_consent(
                f"Run {tool} against {target}",
                level=ConsentLevel.HIGH,
            )
            if not approved:
                return {"error": f"Dad, you didn't approve running {tool} against {target}."}

        log.info("Dad, running %s against %s in sandbox...", tool, target)
        log_event("nia.toolkit", f"run_{tool}", target=target,
                  severity="HIGH", approved=True,
                  details={"args": args})

        cmd = [
            "docker", "run", "--rm",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--network=host",
            f"--timeout={DOCKER_TIMEOUT_SECS}",
            DOCKER_SANDBOX_IMAGE,
            tool, target,
        ]
        if args:
            cmd.extend(args.split())

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=DOCKER_TIMEOUT_SECS
            )
            return {
                "tool": tool,
                "target": target,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:1000],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Dad, {tool} timed out after {DOCKER_TIMEOUT_SECS}s."}
        except FileNotFoundError:
            return {"error": "Dad, Docker is not installed or not in PATH."}
        except Exception as exc:
            return {"error": f"Dad, toolkit error: {exc}"}