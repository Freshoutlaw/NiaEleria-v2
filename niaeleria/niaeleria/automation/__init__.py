# Automation & scheduling
"""
niaeleria/automation/
─────────────────────
NiaEleria's automation layer.

  scheduler.py     — Reminders, recurring tasks, cron-style jobs
  home_control.py  — MQTT-based smart home device control
  briefing.py      — Morning briefing composer (weather + schedule + security)

"Dad, I handle the routine so you can focus on what matters." — Nia
"""

from __future__ import annotations

# ════════════════════════════════════════════════════════════════════
# scheduler.py
# Save as: niaeleria/automation/scheduler.py
# ════════════════════════════════════════════════════════════════════

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional
from uuid import uuid4

from niaeleria.security.kill_switch import assert_alive
from niaeleria.security.audit import log_event

log = logging.getLogger("nia.scheduler")


@dataclass
class Task:
    """A scheduled task for Dad."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    callback: Callable = field(default=lambda: None)
    run_at: Optional[datetime] = None       # One-shot: fire at this time
    interval_secs: Optional[float] = None  # Recurring: fire every N seconds
    next_run: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    last_run: Optional[datetime] = None
    run_count: int = 0


class Scheduler:
    """
    Lightweight cron-like task scheduler.
    Supports one-shot and recurring tasks.
    Checks kill-switch before every execution.

    "Dad, I remember everything you ask me to remind you about — and I never forget." — Nia
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()
        self._running = False

    def add_reminder(
        self,
        name: str,
        callback: Callable,
        run_at: Optional[datetime] = None,
        interval_secs: Optional[float] = None,
        delay_secs: Optional[float] = None,
    ) -> str:
        """
        Schedule a task.
        - run_at:       fire once at a specific datetime
        - interval_secs: fire repeatedly every N seconds
        - delay_secs:   fire once after a delay
        Returns the task ID.
        """
        task = Task(name=name, callback=callback)

        if delay_secs is not None:
            task.run_at = datetime.now() + timedelta(seconds=delay_secs)
            task.next_run = task.run_at
        elif run_at is not None:
            task.run_at = run_at
            task.next_run = run_at
        elif interval_secs is not None:
            task.interval_secs = interval_secs
            task.next_run = datetime.now() + timedelta(seconds=interval_secs)
        else:
            log.warning("Dad, task '%s' has no schedule — it won't run.", name)

        with self._lock:
            self._tasks[task.id] = task

        log.info("Dad, I've scheduled: '%s' (id=%s)", name, task.id)
        log_event("nia.scheduler", "task_scheduled", target=name,
                  details={"id": task.id, "run_at": str(run_at), "interval": interval_secs})
        return task.id

    def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task by ID."""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                log.info("Dad, I've cancelled task %s.", task_id)
                return True
        return False

    def list_tasks(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "next_run": str(t.next_run),
                    "interval_secs": t.interval_secs,
                    "run_count": t.run_count,
                    "enabled": t.enabled,
                }
                for t in self._tasks.values()
            ]

    def start(self) -> None:
        self._running = True
        t = threading.Thread(target=self._loop, name="Scheduler", daemon=True)
        t.start()
        log.info("Dad, my scheduler is running.")

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        while self._running:
            assert_alive()
            now = datetime.now()
            with self._lock:
                due = [t for t in self._tasks.values() if t.enabled and t.next_run <= now]

            for task in due:
                self._fire(task)

            time.sleep(1)

    def _fire(self, task: Task) -> None:
        try:
            log.info("Dad, firing scheduled task: '%s'", task.name)
            task.callback()
            task.last_run = datetime.now()
            task.run_count += 1
            log_event("nia.scheduler", "task_fired", target=task.name,
                      details={"run_count": task.run_count})

            if task.interval_secs:
                task.next_run = datetime.now() + timedelta(seconds=task.interval_secs)
            else:
                # One-shot — disable after firing
                with self._lock:
                    task.enabled = False

        except RuntimeError:
            # Kill-switch mid-task
            self._running = False
        except Exception as exc:
            log.error("Task '%s' failed: %s", task.name, exc)


# ════════════════════════════════════════════════════════════════════
# home_control.py
# Save as: niaeleria/automation/home_control.py
# ════════════════════════════════════════════════════════════════════

import json
import logging as _hc_log

_hc_log = logging.getLogger("nia.home_control")


class HomeController:
    """
    Smart home controller via MQTT.
    Translates natural-language device commands into MQTT messages.
    Supports lights, switches, thermostats, locks, scenes.

    "Dad, your home does what you say — I make sure of it." — Nia
    """

    # Device registry: name → MQTT topic
    # Dad can extend this via the API or config
    _devices: dict[str, str] = {
        "living_room_light": "home/lights/living_room",
        "bedroom_light":     "home/lights/bedroom",
        "front_door_lock":   "home/locks/front_door",
        "thermostat":        "home/climate/thermostat",
        "tv":                "home/appliances/tv",
        "all_lights":        "home/lights/all",
    }

    def __init__(self, mqtt_client) -> None:
        self._mqtt = mqtt_client

    def command(self, device: str, action: str, value: str | int | float | None = None) -> bool:
        """
        Send a command to a smart home device.
        Returns True if published successfully.
        """
        from niaeleria.security.kill_switch import assert_alive
        assert_alive()

        device_key = device.lower().replace(" ", "_")
        topic = self._devices.get(device_key)

        if not topic:
            _hc_log.warning("Dad, I don't know a device called '%s'. Known: %s",
                            device, list(self._devices.keys()))
            return False

        payload = json.dumps({
            "action": action,
            "value": value,
            "source": "nia_voice",
            "ts": datetime.now().isoformat(),
        })

        success = self._mqtt.publish(topic, payload)
        if success:
            _hc_log.info("Dad, sent '%s' → %s (topic: %s)", action, device, topic)
            log_event("nia.home", "device_command", target=device,
                      details={"action": action, "value": value, "topic": topic},
                      approved=True)
        return success

    def parse_natural_language(self, command: str) -> dict | None:
        """
        Parse natural-language home commands.
        e.g. "turn off the living room light" → {device, action, value}
        Simple rule-based parser; the LLM brain handles complex variants.
        """
        cmd = command.lower()
        action = None
        device = None
        value = None

        # Action detection
        if any(w in cmd for w in ("turn on", "switch on", "enable", "open")):
            action = "on"
        elif any(w in cmd for w in ("turn off", "switch off", "disable", "close")):
            action = "off"
        elif "dim" in cmd or "set" in cmd:
            action = "set"
            import re
            match = re.search(r"(\d+)\s*(?:percent|%)?", cmd)
            value = int(match.group(1)) if match else 50
        elif "lock" in cmd:
            action = "lock"
        elif "unlock" in cmd:
            action = "unlock"
        elif any(w in cmd for w in ("temperature", "degrees", "celsius", "heat", "cool")):
            action = "set_temperature"
            import re
            match = re.search(r"(\d+)\s*(?:degrees?|°|c|f)?", cmd)
            value = int(match.group(1)) if match else None

        # Device detection
        for device_key in self._devices:
            if device_key.replace("_", " ") in cmd:
                device = device_key
                break

        if not device:
            if "light" in cmd:
                device = "all_lights"
            elif "door" in cmd or "lock" in cmd:
                device = "front_door_lock"
            elif "thermostat" in cmd or "temperature" in cmd:
                device = "thermostat"
            elif "tv" in cmd or "television" in cmd:
                device = "tv"

        if action and device:
            return {"device": device, "action": action, "value": value}

        return None

    def register_device(self, name: str, mqtt_topic: str) -> None:
        """Dad can add new devices at runtime."""
        self._devices[name.lower().replace(" ", "_")] = mqtt_topic
        _hc_log.info("Dad, I've registered new device '%s' → %s", name, mqtt_topic)


# ════════════════════════════════════════════════════════════════════
# briefing.py
# Save as: niaeleria/automation/briefing.py
# ════════════════════════════════════════════════════════════════════

import logging as _br_log

_br_log = logging.getLogger("nia.briefing")


class MorningBriefing:
    """
    Composes and delivers Dad's morning briefing:
      - Current time & date
      - Weather forecast
      - Today's scheduled tasks
      - Overnight security events
      - Any urgent messages

    "Good morning, Dad. Let me catch you up." — Nia
    """

    def __init__(self, tts, scheduler: Scheduler, guard_status_fn, brain) -> None:
        self._tts = tts
        self._scheduler = scheduler
        self._guard_status_fn = guard_status_fn
        self._brain = brain

    async def deliver(self) -> str:
        """Compose and speak the morning briefing. Returns the text."""
        from niaeleria.security.kill_switch import assert_alive
        assert_alive()

        sections = []
        now = datetime.now()
        sections.append(
            f"Good morning, Dad! It's {now.strftime('%A, %B %d')} at {now.strftime('%I:%M %p')}."
        )

        # Weather
        weather = await self._get_weather()
        if weather:
            sections.append(f"Weather update: {weather}")

        # Today's tasks
        tasks = self._scheduler.list_tasks()
        today_tasks = [
            t for t in tasks
            if t["next_run"] and t["next_run"][:10] == now.strftime("%Y-%m-%d")
        ]
        if today_tasks:
            task_names = ", ".join(t["name"] for t in today_tasks[:5])
            sections.append(f"You have {len(today_tasks)} task(s) today: {task_names}.")
        else:
            sections.append("Your schedule looks clear today, Dad.")

        # Security summary
        try:
            guard = self._guard_status_fn()
            blocked = len(guard.get("blocked_ips", []))
            if blocked:
                sections.append(
                    f"Security note: I blocked {blocked} IP address(es) overnight. "
                    "Check the security dashboard for details."
                )
            else:
                sections.append("Security: all quiet overnight — no threats detected.")
        except Exception as exc:
            _br_log.warning("Guard status error in briefing: %s", exc)

        # Overnight audit events
        from niaeleria.security.audit import tail_log
        overnight = [
            e for e in tail_log(100)
            if e.get("severity") in ("HIGH", "CRITICAL")
        ]
        if overnight:
            sections.append(
                f"Dad, I flagged {len(overnight)} high-severity event(s) overnight. "
                "Please review the audit log when you get a chance."
            )

        briefing_text = " ".join(sections)
        _br_log.info("Delivering morning briefing to Dad.")
        self._tts.speak(briefing_text)

        log_event("nia.briefing", "morning_briefing_delivered", approved=True,
                  details={"length": len(briefing_text)})
        return briefing_text

    async def _get_weather(self) -> str | None:
        """Fetch weather from OpenWeatherMap if network is enabled."""
        from niaeleria.config import OPENWEATHER_API_KEY, DAD_LOCATION, is_network_enabled
        if not is_network_enabled() or not OPENWEATHER_API_KEY:
            return None
        try:
            import httpx
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={DAD_LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric"
            )
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                desc = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                feels = data["main"]["feels_like"]
                return (
                    f"{desc.capitalize()} in {DAD_LOCATION.split(',')[0]}, "
                    f"{temp:.0f}°C, feels like {feels:.0f}°C."
                )
        except Exception as exc:
            _br_log.warning("Weather fetch failed: %s", exc)
            return None