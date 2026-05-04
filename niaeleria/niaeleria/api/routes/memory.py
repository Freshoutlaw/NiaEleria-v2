from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = logging.getLogger("nia.api.memory")
router = APIRouter()


class LearnRequest(BaseModel):
    url: str
    tags: str = ""


class LearnYouTubeRequest(BaseModel):
    url: str


@router.get("/recent")
async def recent_memory(n: int = 20):
    from niaeleria.api.server import _memory
    if not _memory:
        raise HTTPException(status_code=503, detail="Memory not loaded.")
    return _memory.recent_exchanges(n)


@router.get("/search")
async def search_memory(q: str, top_k: int = 10):
    from niaeleria.api.server import _memory, push_to_hud
    if not _memory:
        raise HTTPException(status_code=503, detail="Memory not loaded.")
    results = await _memory.search(q, top_k=top_k)
    if results:
        push_to_hud({
            "type": "show_data",
            "items": [
                {"name": r.get("user", "")[:50], "time": (r.get("ts") or "")[:16]}
                for r in results[:6]
            ],
        })
    return {"query": q, "count": len(results), "results": results}


@router.post("/learn/url")
async def learn_url(req: LearnRequest):
    from niaeleria.api.server import _learner, push_to_hud
    if not _learner:
        raise HTTPException(status_code=503, detail="Learner not available.")

    push_to_hud({
        "type": "nia_speak",
        "text": f"Dad, I'm reading and indexing that page now. I'll let you know what I learn.",
        "label": "NIA · LEARNING",
    })
    summary = await _learner.learn_from_url(req.url, tags=req.tags)
    push_to_hud({
        "type": "nia_speak",
        "text": f"Done, Dad. Here's what I learned: {summary[:200]}{'...' if len(summary) > 200 else ''}",
        "label": "NIA · LEARNED",
    })
    return {"url": req.url, "summary": summary}


@router.post("/learn/youtube")
async def learn_youtube(req: LearnYouTubeRequest):
    from niaeleria.api.server import _learner, push_to_hud
    if not _learner:
        raise HTTPException(status_code=503, detail="Learner not available.")

    push_to_hud({
        "type": "nia_speak",
        "text": "Dad, pulling the transcript from that video now.",
        "label": "NIA · LEARNING",
    })
    summary = await _learner.learn_from_youtube(req.url)
    push_to_hud({
        "type": "nia_speak",
        "text": f"Indexed that video for you, Dad. Summary: {summary[:200]}",
        "label": "NIA · LEARNED",
    })
    return {"url": req.url, "summary": summary}
