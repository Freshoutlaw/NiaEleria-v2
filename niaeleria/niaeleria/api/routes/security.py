from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from niaeleria.security.kill_switch import assert_alive

log = logging.getLogger("nia.api.security")
router = APIRouter()


class BlockRequest(BaseModel):
    ip: str
    reason: str = "manual block by Dad"


class ToolRequest(BaseModel):
    tool: str
    target: str
    args: str = ""


@router.get("/status")
async def guard_status():
    from niaeleria.api.server import _guard, push_to_hud
    from niaeleria.config import is_guard_active, is_killed, is_network_enabled

    status = {
        "guard_active": is_guard_active(),
        "kill_switch": is_killed(),
        "network_enabled": is_network_enabled(),
        "guard": _guard.status() if _guard else {},
    }

    push_to_hud({"type": "status_update", "status": status})
    return status


@router.post("/block")
async def block_ip(req: BlockRequest):
    from niaeleria.guard.cyber_guard import Firewall
    from niaeleria.sync.mqtt_sync import MQTTSync
    from niaeleria.api.server import push_to_hud

    assert_alive()
    success = Firewall.block_ip(req.ip, reason=req.reason, approved=True)
    if success:
        MQTTSync.broadcast_block(req.ip, req.reason)
        push_to_hud({
            "type": "security_alert",
            "data": [{"severity": "HIGH", "action": "MANUAL BLOCK", "target": req.ip}],
        })
    return {"success": success, "ip": req.ip}


@router.delete("/block/{ip}")
async def unblock_ip(ip: str):
    from niaeleria.guard.cyber_guard import Firewall
    from niaeleria.api.server import push_to_hud

    success = Firewall.unblock_ip(ip)
    if success:
        push_to_hud({
            "type": "nia_speak",
            "text": f"Dad, I've unblocked {ip} as you asked.",
            "label": "NIA · FIREWALL",
        })
    return {"success": success, "ip": ip}


@router.get("/blocked")
async def list_blocked():
    from niaeleria.guard.cyber_guard import Firewall
    return {"blocked": Firewall.get_blocked()}


@router.get("/audit")
async def get_audit_log(n: int = 50):
    from niaeleria.security.audit import tail_log, verify_log_integrity
    entries = tail_log(n)
    total, tampered = verify_log_integrity()
    return {"entries": entries, "integrity": {"total": total, "tampered": tampered}}


@router.post("/toolkit/run")
async def run_tool(req: ToolRequest):
    from niaeleria.guard.cyber_guard import SecurityToolkit
    from niaeleria.api.server import push_to_hud

    assert_alive()
    push_to_hud({
        "type": "nia_speak",
        "text": f"Dad, running {req.tool} against {req.target} now.",
        "label": "NIA · TOOLKIT",
    })
    result = SecurityToolkit.run_tool(req.tool, req.target, req.args)
    return result


@router.post("/consent/{approved}")
async def post_consent(approved: bool):
    from niaeleria.security.consent import post_answer
    post_answer(approved)
    return {"received": True, "approved": approved}


@router.post("/kill")
async def activate_kill_switch():
    from niaeleria.config import FLAG_STOP_EVERYTHING
    FLAG_STOP_EVERYTHING.touch()
    return {"kill_switch": "ACTIVATED", "message": "Dad, I'm stopping everything now."}


@router.delete("/kill")
async def deactivate_kill_switch():
    from niaeleria.config import FLAG_STOP_EVERYTHING
    if FLAG_STOP_EVERYTHING.exists():
        FLAG_STOP_EVERYTHING.unlink()
    return {"kill_switch": "CLEARED", "message": "Dad, I'm resuming normal operations."}


@router.post("/network/enable")
async def enable_network():
    from niaeleria.config import FLAG_ENABLE_NETWORK
    from niaeleria.api.server import push_to_hud
    FLAG_ENABLE_NETWORK.touch()
    push_to_hud({"type": "status_update", "status": {"network_enabled": True}})
    push_to_hud({
        "type": "nia_speak",
        "text": "Network access enabled, Dad. I can now reach the internet.",
        "label": "NIA · NETWORK",
    })
    return {"network": "ENABLED"}


@router.post("/network/disable")
async def disable_network():
    from niaeleria.config import FLAG_ENABLE_NETWORK
    from niaeleria.api.server import push_to_hud
    FLAG_ENABLE_NETWORK.unlink(missing_ok=True)
    push_to_hud({"type": "status_update", "status": {"network_enabled": False}})
    push_to_hud({
        "type": "nia_speak",
        "text": "Network access gated, Dad. No external calls will be made.",
        "label": "NIA · NETWORK",
    })
    return {"network": "GATED"}


@router.post("/threat-intel/update")
async def update_threat_intel():
    from niaeleria.guard.cyber_guard import ThreatIntel
    from niaeleria.api.server import push_to_hud

    assert_alive()
    push_to_hud({
        "type": "nia_speak",
        "text": "Updating threat intelligence feed, Dad. Give me a moment.",
        "label": "NIA · THREAT INTEL",
    })
    count = await ThreatIntel.update_feed()
    push_to_hud({
        "type": "nia_speak",
        "text": f"Threat feed updated, Dad. I now have {count:,} known-bad IPs in my list.",
        "label": "NIA · THREAT INTEL",
    })
    return {"loaded": count}
