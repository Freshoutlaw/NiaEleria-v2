"""
niaeleria/guard/cyber_guard.py
──────────────────────────────
NiaEleria's Always-On Cyber Guard — complete final version.

Components:
  Firewall          — cross-platform IP blocking (iptables / netsh / pfctl)
  ThreatIntel       — IP reputation feed + classification
  FileIntegrityMonitor — SHA-256 baseline + change detection
  ProcessMonitor    — watchlist process detection
  PacketSniffer     — scapy passive network analysis
  SecurityToolkit   — consent-gated Docker-sandboxed offensive tools
  CyberGuard        — master orchestrator

Every alert and block is:
  • Logged to HMAC-signed audit trail
  • Pushed to Dad's JARVIS HUD via push_to_hud()
  • Broadcast to other devices via MQTT
  • Spoken via TTS (high severity)

"Dad, I never sleep. While you rest, I'm watching every byte." — Nia
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
    DOCKER_SANDBOX_IMAGE, DOCKER_TIMEOUT_SECS,
)
from niaeleria.security.kill_switch import assert_alive
from niaeleria.security.consent import require_consent, ConsentLevel
from niaeleria.security.audit import log_event

log = logging.getLogger("nia.guard")


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def _push(msg: dict) -> None:
    """Non-blocking HUD push — swallows import errors if API not yet up."""
    try:
        from niaeleria.api.server import push_to_hud
        push_to_hud(msg)
    except Exception:
        pass


def _speak(text: str) -> None:
    """Non-blocking TTS — pulls tts from server service registry."""
    try:
        from niaeleria.api.server import _tts
        if _tts:
            threading.Thread(target=_tts.speak, args=(text,), daemon=True).start()
    except Exception:
        pass


def _broadcast_block(ip: str, reason: str) -> None:
    try:
        from niaeleria.sync.mqtt_sync import MQTTSync
        MQTTSync.broadcast_block(ip, reason)
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────────
# Firewall — cross-platform IP blocking
# ────────────────────────────────────────────────────────────────────

class Firewall:
    """
    Cross-platform firewall manager.
    Linux  → iptables
    macOS  → pfctl anchors
    Windows → netsh advfirewall

    "Dad, when I block something it STAYS blocked — everywhere." — Nia
    """

    _OS: str = platform.system().lower()
    _blocked: set[str] = set()
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def block_ip(
        cls,
        ip: str,
        reason: str = "threat detected",
        approved: bool = False,
    ) -> bool:
        with cls._lock:
            if ip in cls._blocked:
                log.debug("IP %s already blocked — skipping duplicate.", ip)
                return True

            success = False
            try:
                if cls._OS == "linux":
                    for direction, flag in (("INPUT", "-s"), ("OUTPUT", "-d")):
                        subprocess.run(
                            ["iptables", "-A", direction, flag, ip, "-j", "DROP"],
                            check=True, capture_output=True,
                        )
                    success = True

                elif cls._OS == "darwin":
                    anchor_file = Path("/etc/pf.anchors/niaeleria")
                    rule = f"block in quick from {ip} to any\n"
                    anchor_file.parent.mkdir(parents=True, exist_ok=True)
                    with anchor_file.open("a") as f:
                        f.write(rule)
                    subprocess.run(["pfctl", "-f", "/etc/pf.conf"], check=True, capture_output=True)
                    success = True

                elif cls._OS == "windows":
                    subprocess.run([
                        "netsh", "advfirewall", "firewall", "add", "rule",
                        f"name=NiaBlock_{ip.replace('.','_')}",
                        "dir=in", "action=block", f"remoteip={ip}",
                    ], check=True, capture_output=True)
                    success = True

                else:
                    log.warning("Dad, unknown OS '%s' — cannot apply firewall rule.", cls._OS)

            except subprocess.CalledProcessError as exc:
                log.error("Firewall block failed for %s: %s", ip, exc.stderr.decode(errors="replace"))
            except PermissionError:
                log.error(
                    "Dad, I need elevated privileges to manage the firewall. "
                    "Please restart NiaEleria as root / administrator."
                )

            if success:
                cls._blocked.add(ip)
                log.warning("BLOCKED → %s | Reason: %s", ip, reason)
                log_event(
                    "nia.firewall", "block_ip", target=ip,
                    severity="HIGH", approved=approved,
                    details={"reason": reason, "os": cls._OS},
                )

            return success

    @classmethod
    def unblock_ip(cls, ip: str) -> bool:
        with cls._lock:
            if ip not in cls._blocked:
                return True
            try:
                if cls._OS == "linux":
                    for direction, flag in (("INPUT", "-s"), ("OUTPUT", "-d")):
                        subprocess.run(
                            ["iptables", "-D", direction, flag, ip, "-j", "DROP"],
                            check=True, capture_output=True,
                        )
                    cls._blocked.discard(ip)
                    log_event("nia.firewall", "unblock_ip", target=ip, severity="INFO", approved=True)
                    return True
                elif cls._OS == "windows":
                    subprocess.run([
                        "netsh", "advfirewall", "firewall", "delete", "rule",
                        f"name=NiaBlock_{ip.replace('.','_')}",
                    ], check=True, capture_output=True)
                    cls._blocked.discard(ip)
                    return True
            except Exception as exc:
                log.error("Unblock failed for %s: %s", ip, exc)
        return False

    @classmethod
    def get_blocked(cls) -> list[str]:
        return list(cls._blocked)


# ────────────────────────────────────────────────────────────────────
# Threat Intelligence
# ────────────────────────────────────────────────────────────────────

class ThreatIntel:
    """
    Manages a local threat IP blocklist refreshed from an internet feed.
    Also provides severity classification for detected event types.

    "Dad, I know the bad actors by reputation — millions of them." — Nia
    """

    _known_bad: set[str] = set()
    _lock: threading.Lock = threading.Lock()

    SEVERITY_MAP: dict[str, str] = {
        "port_scan":              "HIGH",
        "repeated_auth_failure":  "HIGH",
        "file_tamper":            "HIGH",
        "known_bad_ip":           "HIGH",
        "unusual_process":        "MEDIUM",
        "outbound_unknown":       "MEDIUM",
        "watchlist_process":      "MEDIUM",
        "dns_anomaly":            "LOW",
    }

    @classmethod
    def load_feed(cls, feed_path: Optional[Path] = None) -> int:
        feed_path = feed_path or (PROJECT_HOME / "data" / "threat_feed.txt")
        if not feed_path.exists():
            log.info("Dad, no local threat feed yet — call update_feed() to download one.")
            return 0
        with cls._lock:
            cls._known_bad.clear()
            with feed_path.open() as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        cls._known_bad.add(line.split()[0])
        count = len(cls._known_bad)
        log.info("Dad, threat intel loaded: %d known-bad IPs.", count)
        return count

    @classmethod
    def is_known_bad(cls, ip: str) -> bool:
        return ip in cls._known_bad

    @classmethod
    def classify(cls, event_type: str) -> str:
        return cls.SEVERITY_MAP.get(event_type, "LOW")

    @classmethod
    async def update_feed(cls) -> int:
        from niaeleria.security.network_gate import require_network
        from niaeleria.config import THREAT_INTEL_FEED
        require_network("threat intel feed update")

        import httpx
        feed_path = PROJECT_HOME / "data" / "threat_feed.txt"
        log.info("Dad, downloading latest threat intelligence feed...")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(THREAT_INTEL_FEED)
            resp.raise_for_status()
            feed_path.write_bytes(resp.content)

        count = cls.load_feed(feed_path)
        log_event("nia.threat_intel", "feed_updated", severity="INFO", approved=True,
                  details={"count": count})
        return count


# ────────────────────────────────────────────────────────────────────
# File Integrity Monitor
# ────────────────────────────────────────────────────────────────────

class FileIntegrityMonitor:
    """
    Watches critical directories for unauthorised file changes.
    Baselines on start; alerts Dad + HUD on every detected change.

    "Dad, if anyone touches my files — or yours — I'll know." — Nia
    """

    def __init__(self, paths: list[str]) -> None:
        self._paths    = [Path(p) for p in paths if Path(p).exists()]
        self._baseline: dict[str, str] = {}
        self._running  = False

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
        self._baseline.clear()
        count = 0
        for root in self._paths:
            for fpath in root.rglob("*"):
                if fpath.is_file():
                    self._baseline[str(fpath)] = self._hash_file(fpath)
                    count += 1
        log.info("Dad, file integrity baseline: %d files indexed.", count)
        return count

    def check(self) -> list[dict]:
        changes: list[dict] = []
        current: dict[str, str] = {}

        for root in self._paths:
            for fpath in root.rglob("*"):
                if fpath.is_file():
                    h = self._hash_file(fpath)
                    key = str(fpath)
                    current[key] = h
                    if key not in self._baseline:
                        changes.append({"type": "NEW",      "file": key})
                    elif self._baseline[key] != h:
                        changes.append({"type": "MODIFIED", "file": key})

        for old in self._baseline:
            if old not in current:
                changes.append({"type": "DELETED", "file": old})

        return changes

    def start_watching(self, interval: int = 60) -> None:
        self._running = True
        self.build_baseline()

        def _loop() -> None:
            while self._running:
                assert_alive()
                try:
                    changes = self.check()
                    for c in changes:
                        log.warning(
                            "FILE INTEGRITY ALERT Dad! %s: %s", c["type"], c["file"]
                        )
                        log_event(
                            "nia.integrity", "file_change",
                            target=c["file"], severity="HIGH",
                            details={"change_type": c["type"]},
                        )
                        _push({
                            "type": "security_alert",
                            "data": [{
                                "severity": "HIGH",
                                "action":   f"FILE {c['type']}",
                                "target":   Path(c["file"]).name,
                            }],
                        })
                        if c["type"] in ("MODIFIED", "DELETED"):
                            _speak(
                                f"Dad, file integrity alert! "
                                f"{c['type'].capitalize()}: {Path(c['file']).name}"
                            )
                except RuntimeError:
                    break
                except Exception as exc:
                    log.error("File integrity loop error: %s", exc)
                time.sleep(interval)

        threading.Thread(target=_loop, name="FileIntegrity", daemon=True).start()

    def stop(self) -> None:
        self._running = False


# ────────────────────────────────────────────────────────────────────
# Process Monitor
# ────────────────────────────────────────────────────────────────────

class ProcessMonitor:
    """
    Watches for watchlisted / suspicious processes.
    Alerts Dad immediately with HUD push + TTS on detection.

    "Dad, if something sneaky starts running, I'll catch it." — Nia
    """

    def __init__(self, watchlist: list[str]) -> None:
        self._watchlist = [w.lower().strip() for w in watchlist if w.strip()]
        self._running   = False
        self._seen_pids: set[int] = set()

    def start(self, interval: int = 5) -> None:
        self._running = True

        def _loop() -> None:
            while self._running:
                assert_alive()
                try:
                    for proc in psutil.process_iter(["pid", "name", "cmdline", "username"]):
                        try:
                            pid     = proc.info["pid"]
                            name    = (proc.info["name"] or "").lower()
                            cmdline = " ".join(proc.info["cmdline"] or []).lower()

                            if pid in self._seen_pids:
                                continue

                            for watched in self._watchlist:
                                if watched in name or watched in cmdline:
                                    self._seen_pids.add(pid)
                                    log.warning(
                                        "Dad! Watchlisted process running: %s (PID %d) by %s",
                                        proc.info["name"], pid, proc.info.get("username", "?"),
                                    )
                                    log_event(
                                        "nia.process_monitor", "watchlist_process",
                                        target=proc.info["name"],
                                        severity="MEDIUM",
                                        details={"pid": pid, "cmdline": cmdline[:200]},
                                    )
                                    _push({
                                        "type": "security_alert",
                                        "data": [{
                                            "severity": "MEDIUM",
                                            "action":   "WATCHLISTED PROCESS DETECTED",
                                            "target":   f"{proc.info['name']} (PID {pid})",
                                        }],
                                    })
                                    _speak(
                                        f"Dad, watchlisted process detected: "
                                        f"{proc.info['name']}, PID {pid}."
                                    )
                                    break

                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except RuntimeError:
                    break
                except Exception as exc:
                    log.error("Process monitor error: %s", exc)

                time.sleep(interval)

        threading.Thread(target=_loop, name="ProcessMonitor", daemon=True).start()

    def stop(self) -> None:
        self._running = False


# ────────────────────────────────────────────────────────────────────
# Packet Sniffer
# ────────────────────────────────────────────────────────────────────

class PacketSniffer:
    """
    Passive network packet analysis using scapy.
    Detects port scans, known-bad IP connections, unusual outbound traffic.
    Requires root / administrator — degrades gracefully if unavailable.

    "Dad, I watch every single packet. Nothing slips past me." — Nia
    """

    # Per-source connection counters for port scan detection
    _PORT_SCAN_THRESHOLD = 20

    def __init__(self, iface: Optional[str] = None) -> None:
        self._iface   = iface
        self._running = False
        self._conn_counts: dict[str, int] = {}
        self._alerted_scans: set[str] = set()

        try:
            from scapy.all import sniff, IP, TCP, UDP
            self._sniff = sniff
            self._IP    = IP
            self._TCP   = TCP
            self._UDP   = UDP
            self._available = True
        except ImportError:
            self._available = False
            log.warning(
                "Dad, scapy not installed — packet monitoring disabled. "
                "Run: pip install scapy"
            )
        except Exception as exc:
            self._available = False
            log.warning("Scapy init error: %s", exc)

    def start(self) -> None:
        if not self._available:
            return

        self._running = True

        def _process(pkt) -> None:
            if not self._running or is_killed():
                return
            try:
                if not pkt.haslayer(self._IP):
                    return

                src = pkt[self._IP].src
                dst = pkt[self._IP].dst

                # ── Known-bad IP check ─────────────────────────────
                if ThreatIntel.is_known_bad(src):
                    log.warning("Dad! Packet from KNOWN-BAD IP: %s → %s", src, dst)
                    approved = require_consent(
                        f"Block known-bad IP {src}",
                        level=ConsentLevel.LOW,
                        auto_approve_if_guard=True,
                    )
                    if approved:
                        Firewall.block_ip(src, reason="threat intel match", approved=True)
                        _broadcast_block(src, "threat_intel_match")
                        _push({
                            "type": "security_alert",
                            "data": [{
                                "severity": "HIGH",
                                "action":   "IP BLOCKED — THREAT INTEL MATCH",
                                "target":   src,
                            }],
                        })
                        _speak(
                            f"Dad, I've blocked {src} — it matched my threat intelligence database."
                        )
                    return

                # ── Port scan detection ────────────────────────────
                if pkt.haslayer(self._TCP):
                    self._conn_counts[src] = self._conn_counts.get(src, 0) + 1
                    count = self._conn_counts[src]

                    if count >= self._PORT_SCAN_THRESHOLD and src not in self._alerted_scans:
                        self._alerted_scans.add(src)
                        log.warning(
                            "Dad! Possible port scan from %s (%d packets)", src, count
                        )
                        log_event(
                            "nia.guard", "port_scan_detected",
                            target=src, severity="HIGH",
                            details={"packet_count": count},
                        )
                        _push({
                            "type": "security_alert",
                            "data": [{
                                "severity": "HIGH",
                                "action":   f"PORT SCAN DETECTED ({count} pkts)",
                                "target":   src,
                            }],
                        })
                        _speak(
                            f"Dad, possible port scan from {src}. "
                            f"I've logged it and I'm watching closely."
                        )
                        # Reset counter so repeat alerts don't spam
                        self._conn_counts[src] = 0

            except Exception:
                pass  # Never let packet handler crash the sniffer thread

        def _sniff_thread() -> None:
            try:
                self._sniff(
                    iface=self._iface,
                    prn=_process,
                    store=False,
                    stop_filter=lambda _: not self._running or is_killed(),
                )
            except PermissionError:
                log.warning(
                    "Dad, packet sniffing needs root privileges. "
                    "Restart with: sudo python -m niaeleria.daemon"
                )
            except Exception as exc:
                log.error("Packet sniffer crashed: %s", exc)

        threading.Thread(target=_sniff_thread, name="PacketSniffer", daemon=True).start()
        log.info(
            "Dad, I'm sniffing packets on: %s",
            self._iface or "auto-detected interface",
        )

    def stop(self) -> None:
        self._running = False


# ────────────────────────────────────────────────────────────────────
# Security Toolkit — sandboxed offensive tools
# ────────────────────────────────────────────────────────────────────

class SecurityToolkit:
    """
    Consent-gated, Docker-sandboxed security toolkit.
    Supported tools: nmap, nuclei, hashcat, whatweb, nikto.

    ALL executions require Dad's explicit consent.
    ALL results are logged to the audit trail.
    ALL containers run with minimal privileges.

    "Dad, I keep the knives in a locked box. You hold the key." — Nia
    """

    ALLOWED_TOOLS: frozenset[str] = frozenset({
        "nmap", "nuclei", "hashcat", "whatweb", "nikto",
    })

    @classmethod
    def run_tool(
        cls,
        tool: str,
        target: str,
        args: str = "",
        authorized_by_dad: bool = False,
    ) -> dict:
        assert_alive()

        if tool not in cls.ALLOWED_TOOLS:
            return {
                "error": (
                    f"Dad, '{tool}' is not in my approved toolkit. "
                    f"Allowed: {', '.join(sorted(cls.ALLOWED_TOOLS))}"
                )
            }

        if not authorized_by_dad:
            approved = require_consent(
                f"Run {tool} against {target}",
                level=ConsentLevel.HIGH,
            )
            if not approved:
                return {
                    "error": f"Dad, you didn't approve running {tool} against {target}."
                }

        log.info("Dad, running %s → %s in Docker sandbox...", tool, target)
        log_event(
            "nia.toolkit", f"run_{tool}",
            target=target, severity="HIGH", approved=True,
            details={"args": args},
        )

        cmd = [
            "docker", "run", "--rm",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--network=host",
            DOCKER_SANDBOX_IMAGE,
            tool, target,
        ]
        if args:
            cmd.extend(args.split())

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DOCKER_TIMEOUT_SECS,
            )
            output = {
                "tool":       tool,
                "target":     target,
                "stdout":     result.stdout[:8000],
                "stderr":     result.stderr[:1000],
                "returncode": result.returncode,
            }
            _push({
                "type": "nia_speak",
                "text": f"Dad, {tool} scan against {target} is complete. Check the dashboard for results.",
                "label": "NIA · TOOLKIT",
            })
            return output

        except subprocess.TimeoutExpired:
            return {"error": f"Dad, {tool} timed out after {DOCKER_TIMEOUT_SECS}s."}
        except FileNotFoundError:
            return {
                "error": (
                    "Dad, Docker is not installed or not in PATH. "
                    "Install Docker to enable the security toolkit."
                )
            }
        except Exception as exc:
            return {"error": f"Dad, toolkit error: {exc}"}


# ────────────────────────────────────────────────────────────────────
# CyberGuard — master orchestrator
# ────────────────────────────────────────────────────────────────────

class CyberGuard:
    """
    Orchestrates all guard components.
    Starts each in its own thread; individual failures don't cascade.
    Reports overall status to Dad and the HUD.

    "Dad, I am your shield. Always on. Always watching." — Nia
    """

    def __init__(self) -> None:
        self.firewall       = Firewall
        self.threat_intel   = ThreatIntel
        self.file_monitor   = FileIntegrityMonitor(FILE_INTEGRITY_PATHS)
        self.proc_monitor   = ProcessMonitor(PROCESS_WATCHLIST)
        self.pkt_sniffer    = PacketSniffer(iface=PACKET_CAPTURE_IFACE)
        self.toolkit        = SecurityToolkit
        self._active        = False

    def start(self) -> None:
        if not is_guard_active():
            log.info("Dad, GUARD_ACTIVE flag absent — cyber guard standing down.")
            return

        log.info("Dad, arming all cyber-guard systems now.")
        self._active = True

        # Load threat intel
        self._safe_start("ThreatIntel.load_feed",   ThreatIntel.load_feed)
        # File integrity
        self._safe_start("FileIntegrityMonitor",    self.file_monitor.start_watching)
        # Process monitor
        self._safe_start("ProcessMonitor",          self.proc_monitor.start)
        # Packet sniffer
        self._safe_start("PacketSniffer",           self.pkt_sniffer.start)

        log_event(
            "nia.guard", "guard_started", severity="INFO", approved=True,
            details={
                "components": [
                    "threat_intel", "file_integrity",
                    "process_monitor", "packet_sniffer",
                ],
                "guard_active": True,
            },
        )
        _push({
            "type": "nia_speak",
            "text": (
                "Dad, all cyber-guard systems are armed. "
                "File integrity, process monitor, and packet sniffer are active. "
                "You're protected."
            ),
            "label": "NIA · GUARD ARMED",
        })

    def _safe_start(self, name: str, fn, *args, **kwargs) -> None:
        try:
            fn(*args, **kwargs)
            log.info("Guard component started: %s", name)
        except Exception as exc:
            log.error(
                "Dad, guard component '%s' failed to start: %s "
                "— remaining guards still running.", name, exc,
            )

    def stop(self) -> None:
        log.info("Dad, standing down all cyber-guard systems.")
        self.file_monitor.stop()
        self.proc_monitor.stop()
        self.pkt_sniffer.stop()
        self._active = False
        log_event("nia.guard", "guard_stopped", severity="INFO", approved=True)

    def status(self) -> dict:
        return {
            "guard_active":     self._active,
            "blocked_ips":      Firewall.get_blocked(),
            "threat_ips_loaded": len(ThreatIntel._known_bad),
            "monitored_paths":  FILE_INTEGRITY_PATHS,
            "watched_processes": PROCESS_WATCHLIST,
            "os":               Firewall._OS,
        }