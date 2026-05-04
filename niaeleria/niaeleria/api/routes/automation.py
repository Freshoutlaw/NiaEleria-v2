from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from niaeleria.security.kill_switch import assert_alive

log = logging.getLogger("nia.api.automation")
router = APIRouter()


class ReminderRequest(BaseModel):
    name: str
    message: str
    delay_secs: Optional[float] = None
    run_at_iso: Optional[str] = None
    interval_secs: Optional[float] = None


class DeviceCommand(BaseModel):
    device: str
    action: str
    value: Optional[str] = None


class RegisterDevice(BaseModel):
    name: str
    mqtt_topic: str


class BriefingRequest(BaseModel):
    time_iso: Optional[str] = None


@router.get("/tasks")
async def list_tasks():
    from niaeleria.api.server import _scheduler, push_to_hud
    if not _scheduler:
        return []
    tasks = _scheduler.list_tasks()
    if tasks:
        push_to_hud({"type": "show_data", "items": [
            {"name": t["name"], "time": (t.get("next_run") or "")[:16]}
            for t in tasks[:6]
        ]})
    return tasks


@router.post("/reminder")
async def add_reminder(req: ReminderRequest):
    from niaeleria.api.server import _scheduler, _tts, push_to_hud

    if not _scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available.")

    assert_alive()

    def _remind() -> None:
        msg = f"Dad, reminder: {req.message}"
        if _tts:
            _tts.speak(msg)
        push_to_hud({"type": "nia_speak", "text": msg, "label": "NIA · REMINDER"})

    run_at = datetime.fromisoformat(req.run_at_iso) if req.run_at_iso else None
    task_id = _scheduler.add_reminder(
        name=req.name,
        callback=_remind,
        run_at=run_at,
        interval_secs=req.interval_secs,
        delay_secs=req.delay_secs,
    )
    push_to_hud({
        "type": "nia_speak",
        "text": f"Reminder set, Dad. I'll remind you: {req.message}",
        "label": "NIA · SCHEDULER",
    })
    return {"task_id": task_id, "name": req.name}


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    from niaeleria.api.server import _scheduler, push_to_hud
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available.")
    success = _scheduler.cancel(task_id)
    if success:
        push_to_hud({
            "type": "nia_speak",
            "text": f"Task {task_id} cancelled, Dad.",
            "label": "NIA · SCHEDULER",
        })
    return {"cancelled": success, "task_id": task_id}


@router.post("/home/command")
async def home_command(req: DeviceCommand):
    from niaeleria.api.server import _home_controller, push_to_hud
    if not _home_controller:
        raise HTTPException(status_code=503, detail="Home controller not available.")

    assert_alive()
    success = _home_controller.command(req.device, req.action, req.value)
    if success:
        push_to_hud({
            "type": "nia_speak",
            "text": f"Done, Dad. {req.device} is now {req.action}.",
            "label": "NIA · HOME",
        })
    else:
        push_to_hud({
            "type": "nia_speak",
            "text": f"Dad, I couldn't reach {req.device}. Check the MQTT broker.",
            "label": "NIA · HOME",
        })
    return {"success": success, "device": req.device, "action": req.action}


@router.post("/home/voice")
async def home_voice_command(command: str):
    from niaeleria.api.server import _home_controller, push_to_hud
    if not _home_controller:
        raise HTTPException(status_code=503, detail="Home controller not available.")

    parsed = _home_controller.parse_natural_language(command)
    if not parsed:
        push_to_hud({
            "type": "nia_speak",
            "text": f"Dad, I couldn't figure out what device you meant from: '{command}'",
            "label": "NIA · HOME",
        })
        return {"error": "Could not parse command", "command": command}

    success = _home_controller.command(parsed["device"], parsed["action"], parsed.get("value"))
    push_to_hud({
        "type": "nia_speak",
        "text": f"Done, Dad. {parsed['device'].replace('_',' ')} → {parsed['action']}.",
        "label": "NIA · HOME",
    })
    return {"success": success, **parsed}


@router.post("/home/devices")
async def register_device(req: RegisterDevice):
    from niaeleria.api.server import _home_controller, push_to_hud
    if not _home_controller:
        raise HTTPException(status_code=503, detail="Home controller not available.")
    _home_controller.register_device(req.name, req.mqtt_topic)
    push_to_hud({
        "type": "nia_speak",
        "text": f"Registered new device, Dad: {req.name} on topic {req.mqtt_topic}.",
        "label": "NIA · HOME",
    })
    return {"registered": req.name, "topic": req.mqtt_topic}


@router.post("/briefing")
async def morning_briefing(req: BriefingRequest | None = None):
    from niaeleria.api.server import _brain, _scheduler, _guard, _tts, push_to_hud
    import asyncio, threading

    push_to_hud({
        "type": "nia_speak",
        "text": "Preparing your briefing, Dad. One moment.",
        "label": "NIA · BRIEFING",
    })

    def _run() -> None:
        from niaeleria.automation.briefing import MorningBriefing
        briefing = MorningBriefing(
            tts=_tts,
            scheduler=_scheduler,
            guard_status_fn=lambda: _guard.status() if _guard else {},
            brain=_brain,
        )
        target_at = None
        if req and req.time_iso:
            try:
                target_at = datetime.fromisoformat(req.time_iso)
            except ValueError:
                try:
                    today = datetime.now().date()
                    parsed = datetime.strptime(req.time_iso, "%H:%M")
                    target_at = datetime.combine(today, parsed.time())
                except ValueError:
                    log.warning("Invalid briefing time requested: %s", req.time_iso)
        loop = asyncio.new_event_loop()
        text = loop.run_until_complete(briefing.deliver(target_at=target_at))
        loop.close()
        push_to_hud({"type": "nia_speak", "text": text, "label": "NIA · MORNING BRIEFING"})

    threading.Thread(target=_run, daemon=True, name="ManualBriefing").start()
    return {"status": "briefing started"}
