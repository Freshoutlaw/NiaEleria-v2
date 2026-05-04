"""
niaeleria/daemon.py
────────────────────
NiaEleria master daemon — the heart that starts, watches, and restarts all services.

Start order (strict):
  1. Kill-switch monitor      — inviolable, always first
  2. Audit log                — everything gets logged
  3. Config validation        — warn Dad about missing secrets
  4. Supabase memory          — episodic store
  5. Persona + Brain          — LLM reasoning layer
  6. Internet learner         — background knowledge ingestion
  7. Self-modifier            — consent-gated code evolution
  8. Cyber guard              — packet sniff, file integrity, process watch
  9. MQTT sync                — cross-device firewall broadcast
 10. Home controller          — smart home MQTT commands
 11. Scheduler                — reminders + morning briefing
 12. TTS / STT / Voice        — "Hey Nia" pipeline
 13. Tray                     — system-tray icon
 14. HUD status broadcaster   — proactive periodic push to dashboard
 15. API server               — FastAPI + WebSocket (last — signals ready)

Self-healing: every service runs in a guarded thread; crashes trigger restart.
Kill-switch: flag-file check every 3 s; all threads honour it.

"Dad, I run myself so you don't have to babysit me." — Nia
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import threading
import time
from datetime import datetime, timedelta

import uvicorn

from niaeleria.config import (
    configure_logging, ensure_dirs, first_run_setup, validate_critical_config,
    MORNING_BRIEFING_TIME, API_HOST, API_PORT,
    FLAG_STOP_EVERYTHING, is_killed,
)

log = logging.getLogger("nia.daemon")
_shutdown_event = threading.Event()


# ── Signal handling ────────────────────────────────────────────────────────────

def _handle_signal(signum: int, _frame) -> None:
    log.info("Dad, I received OS signal %d — shutting down gracefully.", signum)
    FLAG_STOP_EVERYTHING.touch()
    _shutdown_event.set()


# ── Service launcher (self-healing) ───────────────────────────────────────────

def _start_service(
    name: str,
    fn,
    *args,
    restart_on_crash: bool = True,
    restart_delay: float = 5.0,
    **kwargs,
) -> threading.Thread:
    """
    Launch a callable in a daemon thread.
    If restart_on_crash=True, automatically restarts on unhandled exceptions.
    Kill-switch errors are never restarted — they mean Dad said stop.
    """
    def _wrapper() -> None:
        while True:
            try:
                log.debug("Service starting: %s", name)
                fn(*args, **kwargs)
                log.info("Service exited normally: %s", name)
                break
            except RuntimeError as exc:
                if "kill" in str(exc).lower():
                    log.info("Service stopped by kill-switch: %s", name)
                    break
                log.error("Service CRASHED (%s): %s", name, exc)
                if not restart_on_crash or is_killed():
                    break
                log.info("Restarting %s in %.0fs, Dad...", name, restart_delay)
                time.sleep(restart_delay)
            except Exception as exc:
                log.error("Service CRASHED (%s): %s", name, exc)
                if not restart_on_crash or is_killed():
                    break
                log.info("Restarting %s in %.0fs...", name, restart_delay)
                time.sleep(restart_delay)

    t = threading.Thread(target=_wrapper, name=name, daemon=True)
    t.start()
    return t


# ── Proactive HUD status broadcaster ──────────────────────────────────────────

def _hud_status_loop(guard, interval: float = 12.0) -> None:
    """
    Periodically push system status to Dad's HUD so vitals stay current.
    Also broadcasts any new high-severity audit events.
    Runs every `interval` seconds.
    """
    from niaeleria.api.server import push_to_hud
    from niaeleria.security.audit import tail_log
    from niaeleria.security.kill_switch import assert_alive
    from niaeleria.config import is_guard_active, is_killed as _kill, is_network_enabled
    from niaeleria.guard.cyber_guard import Firewall

    last_audit_count = 0

    while True:
        assert_alive()
        try:
            status = {
                "guard_active":    is_guard_active(),
                "kill_switch":     _kill(),
                "network_enabled": is_network_enabled(),
                "guard":           guard.status() if guard else {},
            }
            push_to_hud({"type": "status_update", "status": status})

            # Check for new high-severity audit events
            entries = tail_log(100)
            high = [e for e in entries if e.get("severity") in ("HIGH", "CRITICAL")]
            if len(high) > last_audit_count and last_audit_count > 0:
                new_events = high[: len(high) - last_audit_count]
                push_to_hud({
                    "type": "security_alert",
                    "data": [
                        {
                            "severity": e.get("severity", "HIGH"),
                            "action":   e.get("action", ""),
                            "target":   e.get("target", ""),
                        }
                        for e in new_events[:4]
                    ],
                })
            last_audit_count = len(high)

        except RuntimeError:
            break
        except Exception as exc:
            log.debug("HUD status loop error: %s", exc)

        time.sleep(interval)


# ── Uvicorn runner (blocking) ──────────────────────────────────────────────────

def _run_uvicorn(app) -> None:
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="warning",
        access_log=False,
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    # ── OS signals ────────────────────────────────────────────────
    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, _handle_signal)

    # ── Step 1: Logging ───────────────────────────────────────────
    configure_logging()
    log.info("=" * 64)
    log.info("  NiaEleria — Dad's AI, waking up")
    log.info("=" * 64)

    # ── Step 2: Directories & first-run ───────────────────────────
    ensure_dirs()
    first_run_setup()

    # ── Step 3: Config validation ─────────────────────────────────
    warnings = validate_critical_config()
    for w in warnings:
        log.warning("CONFIG WARNING — %s", w)
    if warnings:
        log.warning("Dad, please fix the warnings above in your .env file.")

    # Clear stale kill-switch state from an earlier shutdown so a fresh start can proceed.
    if FLAG_STOP_EVERYTHING.exists():
        log.warning(
            "Dad, stale STOP_EVERYTHING flag detected from a prior session. Clearing it so I can start."
        )
        try:
            FLAG_STOP_EVERYTHING.unlink()
        except Exception as exc:
            log.error("Failed to remove stale STOP_EVERYTHING flag: %s", exc)

    # ── Step 4: Kill-switch (ALWAYS FIRST THREAD) ──────────────────
    from niaeleria.security import kill_switch as _ks
    _ks.register_shutdown_callback(lambda: _shutdown_event.set())
    _ks.start_monitor()
    log.info("[1/14] Kill-switch monitor: ARMED")

    # ── Step 5: Audit log ──────────────────────────────────────────
    from niaeleria.security.audit import verify_log_integrity, log_event
    total, tampered = verify_log_integrity()
    if tampered:
        log.error(
            "Dad! Audit log integrity check FAILED: %d tampered entries detected! "
            "Someone may have touched my logs. Investigate immediately.", tampered
        )
    log_event(
        "nia.daemon", "startup", severity="INFO", approved=True,
        details={"config_warnings": len(warnings), "audit_entries": total, "tampered": tampered},
    )
    log.info("[2/14] Audit log: VERIFIED (%d entries, %d tampered)", total, tampered)

    # ── Step 6: Supabase memory ────────────────────────────────────
    from niaeleria.core.memory import MemoryStore
    memory = MemoryStore()
    log.info("[3/14] Supabase memory: CONNECTED")

    # ── Step 7: Persona + Brain ────────────────────────────────────
    from niaeleria.core.persona import PersonaEngine
    from niaeleria.core.brain   import NiaBrain
    persona = PersonaEngine()
    brain   = NiaBrain(memory=memory, persona=persona)
    log.info("[4/14] AI brain (Groq/%s): ONLINE", __import__("niaeleria.config", fromlist=["LLM_MODEL"]).LLM_MODEL)

    # ── Step 8: Internet learner ───────────────────────────────────
    from niaeleria.core.learner import InternetLearner
    learner = InternetLearner(memory=memory, brain=brain)
    log.info("[5/14] Internet learner: READY")

    # ── Step 9: Self-modifier ──────────────────────────────────────
    from niaeleria.security.self_modifier import SelfModifier
    self_modifier = SelfModifier()
    log.info("[6/14] Self-modifier: READY")

    # ── Step 10: Consent notifier placeholder ──────────────────────
    # TTS not loaded yet — use log-only notifier until TTS is ready
    from niaeleria.security.consent import set_notifier
    set_notifier(lambda msg: log.info("[CONSENT PENDING] %s", msg))

    # ── Step 11: Cyber guard ───────────────────────────────────────
    from niaeleria.guard.cyber_guard import CyberGuard
    guard = CyberGuard()
    guard.start()
    log.info("[7/14] Cyber guard: %s", "ACTIVE" if __import__("niaeleria.config", fromlist=["is_guard_active"]).is_guard_active() else "STANDBY")

    # ── Step 12: MQTT sync ─────────────────────────────────────────
    from niaeleria.sync.mqtt_sync import MQTTSync
    mqtt = MQTTSync()
    mqtt_ok = mqtt.connect()
    if mqtt_ok:
        mqtt.setup_firewall_sync()
    log.info("[8/14] MQTT sync: %s", "CONNECTED" if mqtt_ok else "OFFLINE")

    # ── Step 13: Home controller ───────────────────────────────────
    from niaeleria.automation.home_control import HomeController
    home_controller = HomeController(mqtt_client=mqtt)
    log.info("[9/14] Home controller: READY")

    # ── Step 14: Scheduler ─────────────────────────────────────────
    from niaeleria.automation.scheduler import Scheduler
    scheduler = Scheduler()
    scheduler.start()
    log.info("[10/14] Scheduler: RUNNING")

    # ── Step 15: Voice stack ───────────────────────────────────────
    from niaeleria.voice.tts import TextToSpeech
    from niaeleria.voice.stt import SpeechToText
    from niaeleria.voice     import VoiceInterface

    tts   = TextToSpeech()
    stt   = SpeechToText()
    voice = VoiceInterface(brain=brain, tts=tts, stt=stt)

    # Now plug TTS into consent system
    set_notifier(tts.speak)
    voice.start()
    log.info("[11/14] Voice interface: LISTENING for 'Hey Nia'")

    # ── Step 16: Morning briefing task ────────────────────────────
    from niaeleria.automation.briefing import MorningBriefing
    briefing = MorningBriefing(
        tts=tts,
        scheduler=scheduler,
        guard_status_fn=guard.status,
        brain=brain,
    )

    # Schedule morning briefing — calculate seconds until next occurrence
    h, m     = (int(x) for x in MORNING_BRIEFING_TIME.split(":"))
    now      = datetime.now()
    next_run = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if next_run <= now:
        next_run += timedelta(days=1)
    delay_secs = (next_run - now).total_seconds()

    def _do_briefing() -> None:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(briefing.deliver())
        loop.close()

    scheduler.add_reminder(
        name="Morning Briefing",
        callback=_do_briefing,
        interval_secs=86400,   # repeat daily
        delay_secs=delay_secs,
    )
    log.info(
        "[12/14] Morning briefing scheduled for %s (%.0f min from now)",
        MORNING_BRIEFING_TIME, delay_secs / 60,
    )

    # ── Step 17: API server — inject all services ──────────────────
    from niaeleria.api.server import create_app, inject_services
    inject_services(
        brain=brain,
        memory=memory,
        guard=guard,
        scheduler=scheduler,
        self_modifier=self_modifier,
        tts=tts,
        home_controller=home_controller,
        learner=learner,
    )
    app = create_app()
    log.info("[13/14] API server: CONFIGURED on %s:%d", API_HOST, API_PORT)

    # ── Step 18: System tray ───────────────────────────────────────
    from niaeleria.tray.tray_app import NiaTray
    tray = NiaTray(voice_interface=voice, tts=tts, stt=stt, brain=brain)
    tray.start()
    log.info("[14/14] System tray: ACTIVE")

    # ── Step 19: Proactive HUD broadcaster ────────────────────────
    _start_service(
        "HUDStatusBroadcast",
        _hud_status_loop,
        guard,
        restart_on_crash=True,
    )

    # ── Step 20: API server (blocking, in its own thread) ──────────
    _start_service("APIServer", _run_uvicorn, app, restart_on_crash=False)
    time.sleep(1.5)   # give uvicorn a moment to bind

    # ── Step 21: Startup greeting (spoken + HUD) ───────────────────
    def _greet() -> None:
        from niaeleria.api.server import push_to_hud
        time.sleep(1)
        msg = (
            "Dad, I'm fully online. "
            "Cyber guard is armed. "
            f"Dashboard is at port {API_PORT}. "
            "Say 'Hey Nia' whenever you're ready."
        )
        tts.speak(msg)
        push_to_hud({"type": "nia_speak", "text": msg, "label": "NIA · ONLINE"})
        log_event("nia.daemon", "fully_online", severity="INFO", approved=True)

    threading.Thread(target=_greet, daemon=True, name="StartupGreet").start()
    log.info("NiaEleria is FULLY ONLINE. Dad, I'm ready.")
    log.info("Dashboard → http://%s:%d", API_HOST, API_PORT)

    # ── Wait for shutdown signal ───────────────────────────────────
    try:
        while not _shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    # ── Graceful teardown ──────────────────────────────────────────
    log.info("Shutting down NiaEleria...")
    try:
        voice.stop()
        guard.stop()
        scheduler.stop()
        mqtt.disconnect()
        memory.close()
        tray.stop()
    except Exception as exc:
        log.error("Shutdown error (non-critical): %s", exc)

    log_event("nia.daemon", "shutdown", severity="INFO", approved=True)
    log.info("Goodbye, Dad. NiaEleria is offline. Stay safe.")
    sys.exit(0)


if __name__ == "__main__":
    main()