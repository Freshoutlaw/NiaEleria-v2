"""
niaeleria/automation/briefing.py
─────────────────────────────────
NiaEleria's morning briefing — speaks to Dad AND pushes to the HUD.
Weather · Schedule · Security · Audit highlights.

"Good morning, Dad. Let me catch you up." — Nia
"""

from __future__ import annotations

import logging
from datetime import datetime

log = logging.getLogger("nia.briefing")


class MorningBriefing:
    """
    Composes and delivers Dad's morning briefing.
    - Speaks via TTS
    - Pushes sections to the JARVIS HUD in sequence
    - Logs delivery to audit trail
    """

    def __init__(self, tts, scheduler, guard_status_fn, brain) -> None:
        self._tts             = tts
        self._scheduler       = scheduler
        self._guard_status_fn = guard_status_fn
        self._brain           = brain

    async def deliver(self, target_at: datetime | None = None) -> str:
        from niaeleria.security.kill_switch import assert_alive
        from niaeleria.security.audit import log_event
        from niaeleria.api.server import push_to_hud

        assert_alive()

        sections: list[str] = []
        now = target_at or datetime.now()

        # ── Greeting ────────────────────────────────────────────────
        if target_at:
            greeting = (
                f"Good {self._get_daypart(now.hour)}, Dad. "
                f"Here's your briefing for {now.strftime('%A, %B %d at %I:%M %p')}."
            )
        else:
            greeting = (
                f"Good {self._get_daypart(now.hour)}, Dad. "
                f"It's {now.strftime('%A, %B %d')} at {now.strftime('%I:%M %p')}."
            )
        sections.append(greeting)
        push_to_hud({"type": "nia_speak", "text": greeting, "label": "NIA · MORNING"})

        # ── Weather ─────────────────────────────────────────────────
        weather = await self._get_weather()
        if weather:
            sections.append(weather)
            push_to_hud({"type": "nia_speak", "text": weather, "label": "NIA · WEATHER"})

        # ── Schedule ────────────────────────────────────────────────
        tasks = self._scheduler.list_tasks() if self._scheduler else []
        today_str = now.strftime("%Y-%m-%d")
        today_tasks = [
            t for t in tasks
            if (t.get("next_run") or "").startswith(today_str)
        ]

        if today_tasks:
            task_section = (
                f"You have {len(today_tasks)} task{'s' if len(today_tasks)!=1 else ''} "
                f"scheduled today, Dad: "
                + ", ".join(t["name"] for t in today_tasks[:5])
                + "."
            )
            push_to_hud({
                "type": "show_data",
                "items": [
                    {"name": t["name"], "time": (t.get("next_run") or "")[:16]}
                    for t in today_tasks[:6]
                ],
            })
        else:
            task_section = "Your schedule looks clear today, Dad."

        sections.append(task_section)
        push_to_hud({"type": "nia_speak", "text": task_section, "label": "NIA · SCHEDULE"})

        # ── Security summary ─────────────────────────────────────────
        try:
            guard = self._guard_status_fn()
            blocked_count = len(guard.get("blocked_ips", []))
            if blocked_count:
                sec_msg = (
                    f"Security update: I blocked {blocked_count} "
                    f"IP address{'es' if blocked_count != 1 else ''} overnight. "
                    "Check the security dashboard for details, Dad."
                )
                push_to_hud({
                    "type": "security_alert",
                    "data": [
                        {"severity": "MEDIUM", "action": f"{blocked_count} IPs BLOCKED OVERNIGHT", "target": ""}
                    ],
                })
            else:
                sec_msg = "Security is all clear overnight, Dad. No threats detected."

            sections.append(sec_msg)
            push_to_hud({"type": "nia_speak", "text": sec_msg, "label": "NIA · SECURITY"})
        except Exception as exc:
            log.warning("Guard status error in briefing: %s", exc)

        # ── High-severity audit events ───────────────────────────────
        try:
            from niaeleria.security.audit import tail_log
            high_sev = [
                e for e in tail_log(200)
                if e.get("severity") in ("HIGH", "CRITICAL")
            ]
            if high_sev:
                audit_msg = (
                    f"Dad, I flagged {len(high_sev)} high-severity "
                    f"event{'s' if len(high_sev)!=1 else ''} overnight. "
                    "Please review the audit log when you get a chance."
                )
                sections.append(audit_msg)
                push_to_hud({"type": "nia_speak", "text": audit_msg, "label": "NIA · AUDIT"})
        except Exception as exc:
            log.warning("Audit log error in briefing: %s", exc)

        # ── Closing ──────────────────────────────────────────────────
        closing = "That's your morning briefing, Dad. I'm here if you need anything."
        sections.append(closing)
        push_to_hud({"type": "nia_speak", "text": closing, "label": "NIA · BRIEFING"})

        # ── Speak it all (TTS) ───────────────────────────────────────
        full_text = " ".join(sections)
        if self._tts:
            self._tts.speak(full_text)

        log_event(
            "nia.briefing", "morning_briefing_delivered",
            severity="INFO", approved=True,
            details={"requested_for": now.isoformat(), "sections": len(sections), "length": len(full_text)},
        )
        log.info("Morning briefing delivered to Dad. %d sections.", len(sections))
        return full_text

    @staticmethod
    def _get_daypart(hour: int) -> str:
        if hour < 12:
            return "morning"
        if hour < 18:
            return "afternoon"
        return "evening"

    async def _get_weather(self) -> str | None:
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
            desc   = data["weather"][0]["description"]
            temp   = data["main"]["temp"]
            feels  = data["main"]["feels_like"]
            humid  = data["main"]["humidity"]
            city   = DAD_LOCATION.split(",")[0]
            return (
                f"Weather in {city}: {desc.capitalize()}, "
                f"{temp:.0f}°C, feels like {feels:.0f}°C, humidity {humid}%."
            )
        except Exception as exc:
            log.warning("Weather fetch failed: %s", exc)
            return None