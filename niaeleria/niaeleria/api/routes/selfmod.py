from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = logging.getLogger("nia.api.selfmod")
router = APIRouter()


class ProposeRequest(BaseModel):
    file_rel_path: str
    new_content: str
    reason: str


class ApplyRequest(BaseModel):
    file_rel_path: str
    new_content: str
    proposal_id: str


@router.post("/propose")
async def propose_change(req: ProposeRequest):
    from niaeleria.api.server import _self_modifier, push_to_hud
    if not _self_modifier:
        raise HTTPException(status_code=503, detail="Self-modifier not available.")

    proposal = _self_modifier.propose_change(req.file_rel_path, req.new_content, req.reason)
    if "error" not in proposal:
        push_to_hud({
            "type": "nia_speak",
            "text": (
                f"Dad, I have a proposed change to {req.file_rel_path}. "
                f"Reason: {req.reason}. Proposal ID: {proposal.get('proposal_id')}. "
                "Please review and approve or deny via the apply endpoint."
            ),
            "label": "NIA · SELF-MODIFICATION",
        })
    return proposal


@router.post("/apply")
async def apply_change(req: ApplyRequest):
    from niaeleria.api.server import _self_modifier, push_to_hud
    if not _self_modifier:
        raise HTTPException(status_code=503, detail="Self-modifier not available.")

    result = _self_modifier.apply_change(req.file_rel_path, req.new_content, req.proposal_id)
    if result.get("success"):
        push_to_hud({
            "type": "nia_speak",
            "text": (
                f"Code change applied to {req.file_rel_path}, Dad. "
                f"Backup saved. {result.get('reload', '')}. I'm already running the update."
            ),
            "label": "NIA · SELF-MODIFICATION",
        })
    return result


@router.post("/rollback")
async def rollback(file_rel_path: str):
    from niaeleria.api.server import _self_modifier, push_to_hud
    if not _self_modifier:
        raise HTTPException(status_code=503, detail="Self-modifier not available.")

    result = _self_modifier.rollback(file_rel_path)
    if result.get("success"):
        push_to_hud({
            "type": "nia_speak",
            "text": f"Rolled back {file_rel_path} to its last backup, Dad. All good.",
            "label": "NIA · SELF-MODIFICATION",
        })
    return result


@router.get("/backups")
async def list_backups():
    from niaeleria.config import BACKUPS_DIR
    backups = sorted(BACKUPS_DIR.glob("*.backup"), reverse=True)
    return {
        "backups": [
            {"name": b.name, "size_kb": round(b.stat().st_size / 1024, 1)}
            for b in backups[:50]
        ]
    }
