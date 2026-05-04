from __future__ import annotations

import logging
import platform
import subprocess
import threading

from niaeleria.security.audit import log_event

log = logging.getLogger("nia.guard")


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
