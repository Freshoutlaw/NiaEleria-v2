from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from niaeleria.security.kill_switch import assert_alive

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ChatResponse(BaseModel):
    response: str
    mood: str = "warm"


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    from niaeleria.api.server import _brain, push_to_hud
    assert_alive()
    if not _brain:
        raise HTTPException(status_code=503, detail="Dad, my brain isn't loaded yet.")

    push_to_hud({"type": "thinking"})
    response = await _brain.chat(req.message, req.history)
    push_to_hud({"type": "nia_speak", "text": response, "label": "NIA · RESPONSE"})
    return ChatResponse(response=response)


@router.get("/history")
async def get_history(n: int = 20):
    from niaeleria.api.server import _memory
    if not _memory:
        return []
    return _memory.recent_exchanges(n)
