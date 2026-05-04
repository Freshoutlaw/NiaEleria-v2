# ════════════════════════════════════════════════════════════════════
# consent.py — Consent manager for all gated operations
# ════════════════════════════════════════════════════════════════════
# Save as: niaeleria/security/consent.py

import logging
import queue
from enum import Enum
from typing import Callable

from niaeleria.security.kill_switch import assert_alive

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