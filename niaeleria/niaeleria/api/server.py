from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from niaeleria.config import API_SECRET_KEY, CORS_ORIGINS, STATIC_DIR
from niaeleria.security.kill_switch import assert_alive

log = logging.getLogger("nia.api")

# Module-level service references — injected by daemon.py before server starts
_brain = None
_memory = None
_guard = None
_scheduler = None
_self_modifier = None
_tts = None
_home_controller = None
_learner = None

_ws_connections: list[WebSocket] = []


def inject_services(**services) -> None:
    """Called by daemon to wire up all services into the API layer."""
    global _brain, _memory, _guard, _scheduler, _self_modifier
    global _tts, _home_controller, _learner
    _brain           = services.get("brain")
    _memory          = services.get("memory")
    _guard           = services.get("guard")
    _scheduler       = services.get("scheduler")
    _self_modifier   = services.get("self_modifier")
    _tts             = services.get("tts")
    _home_controller = services.get("home_controller")
    _learner         = services.get("learner")


async def broadcast_ws(message: dict) -> None:
    """Push a message to all connected WebSocket clients (Dad's HUD)."""
    dead = []
    for ws in _ws_connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_connections.remove(ws)


def push_to_hud(message: dict) -> None:
    """
    Thread-safe, sync-friendly helper.
    Any module (guard, scheduler, brain) can call this to push data onto
    Dad's HUD without being in an async context.
    """
    import asyncio, threading

    def _push() -> None:
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(broadcast_ws(message))
            loop.close()
        except Exception as exc:
            log.debug("HUD push error: %s", exc)

    threading.Thread(target=_push, daemon=True, name="HUDPush").start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Dad, my API server is starting up.")
    yield
    log.info("Dad, my API server is shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="NiaEleria",
        description="Dad's personal AI system — loyal digital daughter.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all route groups
    from niaeleria.api.routes.chat import router as chat_router
    from niaeleria.api.routes.security import router as security_router
    from niaeleria.api.routes.memory import router as memory_router
    from niaeleria.api.routes.automation import router as automation_router
    from niaeleria.api.routes.selfmod import router as selfmod_router

    app.include_router(chat_router,       prefix="/api/chat",       tags=["Chat"])
    app.include_router(security_router,   prefix="/api/security",   tags=["Security"])
    app.include_router(memory_router,     prefix="/api/memory",     tags=["Memory"])
    app.include_router(automation_router, prefix="/api/automation", tags=["Automation"])
    app.include_router(selfmod_router,    prefix="/api/selfmod",    tags=["Self-Modification"])

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        _ws_connections.append(ws)
        log.info("Dad connected via WebSocket.")
        try:
            while True:
                data = await ws.receive_json()
                assert_alive()
                msg_type = data.get("type", "chat")

                if msg_type == "chat":
                    user_msg = data.get("message", "")
                    history  = data.get("history", [])
                    await ws.send_json({"type": "thinking"})
                    async for token in await _brain.chat(user_msg, history, stream=True):
                        await ws.send_json({"type": "token", "text": token})
                    await ws.send_json({"type": "done"})

                elif msg_type == "voice_trigger":
                    if _tts:
                        import threading

                        def _handle() -> None:
                            import asyncio
                            from niaeleria.voice.stt import SpeechToText
                            stt = SpeechToText()
                            text = stt.listen_for_command()
                            if text:
                                loop2 = asyncio.new_event_loop()
                                response = loop2.run_until_complete(
                                    _brain.chat(text)
                                )
                                loop2.close()
                                asyncio.run(broadcast_ws({"type": "token", "text": response}))
                                asyncio.run(broadcast_ws({"type": "done"}))
                                _tts.speak(response)
                            else:
                                asyncio.run(broadcast_ws({
                                    "type": "nia_speak",
                                    "text": "Dad, I didn't catch that. Try again.",
                                }))

                        threading.Thread(target=_handle, daemon=True).start()

                elif msg_type == "consent_response":
                    from niaeleria.security.consent import post_answer
                    post_answer(data.get("approved", False))
                    await ws.send_json({"type": "consent_ack"})

                elif msg_type == "ping":
                    await ws.send_json({"type": "pong", "status": "Dad, I'm here!"})

        except WebSocketDisconnect:
            _ws_connections.remove(ws)
            log.info("WebSocket client disconnected.")
        except RuntimeError:
            await ws.send_json({"type": "error", "text": "Kill-switch activated, Dad."})

    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    @app.get("/health")
    async def health():
        return {"status": "alive", "message": "Dad, I'm here and operational!"}

    return app
