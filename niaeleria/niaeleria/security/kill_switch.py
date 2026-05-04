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

