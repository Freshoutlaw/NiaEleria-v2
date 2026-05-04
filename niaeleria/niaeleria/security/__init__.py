# Security & consent subsystems
"""
niaeleria/security/__init__.py + kill_switch.py + consent.py + audit.py + network_gate.py
──────────────────────────────────────────────────────────────────────────────────────────
NiaEleria's Security Framework — the inviolable core that keeps Dad safe.

"Dad, these rules are the ones I will NEVER break, no matter what anyone asks." — Nia
"""

# ════════════════════════════════════════════════════════════════════
# kill_switch.py — STOP_EVERYTHING poller
# ════════════════════════════════════════════════════════════════════
# Save as: niaeleria/security/kill_switch.py

from __future__ import annotations
import logging
import threading
import time
from typing import Callable
from niaeleria.config import (
    FLAG_STOP_EVERYTHING, KILL_SWITCH_POLL_INTERVAL, is_killed
)

log = logging.getLogger("nia.kill_switch")

_callbacks: list[Callable[[], None]] = []
_monitor_thread: threading.Thread | None = None
_running = False


def register_shutdown_callback(cb: Callable[[], None]) -> None:
    """Register a function to call the moment kill-switch is detected."""
    _callbacks.append(cb)


def assert_alive() -> None:
    """
    Call this at the top of every loop and before every significant action.
    Raises RuntimeError if Dad has activated the kill-switch.
    """
    if is_killed():
        raise RuntimeError(
            "Kill-switch ACTIVE — Dad, I'm stopping everything immediately as you commanded."
        )


def start_monitor(poll_interval: float = KILL_SWITCH_POLL_INTERVAL) -> None:
    """
    Start the background kill-switch monitor thread.
    Fires all registered shutdown callbacks when STOP_EVERYTHING is detected.
    """
    global _monitor_thread, _running

    def _loop() -> None:
        global _running
        log.info("Dad, my kill-switch monitor is armed and watching.")
        while _running:
            if FLAG_STOP_EVERYTHING.exists():
                log.critical(
                    "Dad, I see the STOP_EVERYTHING flag! Executing full shutdown NOW."
                )
                for cb in _callbacks:
                    try:
                        cb()
                    except Exception as exc:
                        log.error("Shutdown callback error: %s", exc)
                _running = False
                break
            time.sleep(poll_interval)

    _running = True
    _monitor_thread = threading.Thread(target=_loop, name="KillSwitchMonitor", daemon=True)
    _monitor_thread.start()


def stop_monitor() -> None:
    global _running
    _running = False


# ════════════════════════════════════════════════════════════════════
# audit.py — HMAC-SHA256 append-only audit log
# ════════════════════════════════════════════════════════════════════
# Save as: niaeleria/security/audit.py

import hashlib
import hmac as _hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from niaeleria.config import AUDIT_LOG, AUDIT_HMAC_KEY

_audit_log = logging.getLogger("nia.audit")
_write_lock = threading.Lock()


def _sign(entry: str) -> str:
    """Return HMAC-SHA256 hex digest of the log entry string."""
    return _hmac.new(AUDIT_HMAC_KEY, entry.encode(), hashlib.sha256).hexdigest()


def log_event(
    actor: str,
    action: str,
    target: str = "",
    severity: str = "INFO",
    details: dict | None = None,
    approved: bool = False,
) -> None:
    """
    Append a signed event to the audit log.
    Every destructive, external, or security event must call this, Dad.
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "target": target,
        "severity": severity,
        "approved": approved,
        "details": details or {},
    }
    entry = json.dumps(record, separators=(",", ":"))
    sig = _sign(entry)
    line = f"{entry}|SIG:{sig}\n"

    with _write_lock:
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(line)

    _audit_log.info("AUDIT [%s] %s → %s (approved=%s)", severity, actor, action, approved)


def verify_log_integrity() -> tuple[int, int]:
    """
    Scan audit log and verify every entry's HMAC signature.
    Returns (total_entries, tampered_count).
    Dad can call this any time to confirm I haven't been messed with.
    """
    if not AUDIT_LOG.exists():
        return 0, 0

    total, tampered = 0, 0
    with AUDIT_LOG.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            if "|SIG:" not in line:
                _audit_log.warning("Line %d missing signature!", line_num)
                tampered += 1
                continue
            entry, sig = line.rsplit("|SIG:", 1)
            expected = _sign(entry)
            if not _hmac.compare_digest(expected, sig):
                _audit_log.error("TAMPERED entry at line %d!", line_num)
                tampered += 1

    return total, tampered


def tail_log(n: int = 50) -> list[dict]:
    """Return the last n audit log entries as parsed dicts (for API/UI consumption)."""
    if not AUDIT_LOG.exists():
        return []
    lines = AUDIT_LOG.read_text(encoding="utf-8").strip().splitlines()
    results = []
    for line in lines[-n:]:
        if "|SIG:" in line:
            entry, _ = line.rsplit("|SIG:", 1)
            try:
                results.append(json.loads(entry))
            except json.JSONDecodeError:
                pass
    return results


# ════════════════════════════════════════════════════════════════════
# network_gate.py — External connectivity enforcement
# ════════════════════════════════════════════════════════════════════
# Save as: niaeleria/security/network_gate.py

_net_log = logging.getLogger("nia.network_gate")


def require_network(purpose: str = "external call") -> None:
    """
    Raise PermissionError if ENABLE_NETWORK flag is absent.
    Call this before ANY external HTTP/socket connection, Dad.
    """
    from niaeleria.config import is_network_enabled
    if not is_network_enabled():
        _net_log.warning(
            "Dad, I blocked an external call (%s) — ENABLE_NETWORK flag is not set. "
            "Touch flags/ENABLE_NETWORK to allow me online.", purpose
        )
        raise PermissionError(
            f"Network gate: external access denied for '{purpose}'. "
            "Dad, please create the ENABLE_NETWORK flag file to allow this."
        )
    _net_log.debug("Network gate: PASS for '%s'", purpose)


# ════════════════════════════════════════════════════════════════════
# consent.py — Consent manager for all gated operations
# ════════════════════════════════════════════════════════════════════
# Save as: niaeleria/security/consent.py

import queue
from enum import Enum

_consent_log = logging.getLogger("nia.consent")

# Queue where the API/UI posts Dad's answers
_consent_queue: queue.Queue[bool] = queue.Queue()

# Pluggable notifier — replaced by voice/TTS module at runtime
_notifier: Callable[[str], None] | None = None


class ConsentLevel(str, Enum):
    LOW = "low"        # Auto-approved when guard is active (e.g., block a known bad IP)
    MEDIUM = "medium"  # Requires Dad's approval via notification
    HIGH = "high"      # Requires Dad's explicit typed confirmation + audit


def set_notifier(fn: Callable[[str], None]) -> None:
    """Plug in TTS/notification system so consent requests reach Dad audibly."""
    global _notifier
    _notifier = fn


def _notify_dad(message: str) -> None:
    if _notifier:
        try:
            _notifier(message)
        except Exception as exc:
            _consent_log.error("Notifier error: %s", exc)
    _consent_log.info("CONSENT REQUEST → Dad: %s", message)


def post_answer(approved: bool) -> None:
    """Called by API route when Dad responds to a consent prompt."""
    _consent_queue.put(approved)


def require_consent(
    action: str,
    level: ConsentLevel = ConsentLevel.MEDIUM,
    auto_approve_if_guard: bool = False,
    timeout: int | None = None,
) -> bool:
    """
    Gate any action behind Dad's consent.

    - LOW severity + guard active + auto_approve_if_guard → returns True immediately.
    - Otherwise: notifies Dad and waits for his response.
    - Returns False on timeout or denial.

    "Dad, I will always ask before doing anything that matters." — Nia
    """
    from niaeleria.config import is_guard_active, is_killed, CONSENT_TIMEOUT_SECS
    assert_alive()

    if level == ConsentLevel.LOW and auto_approve_if_guard and is_guard_active():
        _consent_log.info(
            "Auto-approved (LOW severity, guard active): %s", action
        )
        from niaeleria.security.audit import log_event
        log_event("nia.consent", action, severity="LOW", approved=True,
                  details={"reason": "auto-approved by guard policy"})
        return True

    timeout = timeout or CONSENT_TIMEOUT_SECS
    _notify_dad(
        f"Dad, I need your permission to: {action}. "
        f"Please respond YES or NO within {timeout} seconds."
    )

    try:
        # Drain stale answers first
        while not _consent_queue.empty():
            _consent_queue.get_nowait()

        approved: bool = _consent_queue.get(timeout=timeout)
    except queue.Empty:
        _consent_log.warning("Consent timeout for: %s — defaulting to DENY", action)
        approved = False

    from niaeleria.security.audit import log_event
    log_event(
        "nia.consent", action, severity=level.value.upper(), approved=approved
    )

    if approved:
        _consent_log.info("Dad approved: %s", action)
    else:
        _consent_log.info("Dad denied (or timeout): %s", action)

    return approved