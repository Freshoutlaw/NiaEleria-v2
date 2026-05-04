from .chat import router as chat_router
from .security import router as security_router
from .memory import router as memory_router
from .automation import router as automation_router
from .selfmod import router as selfmod_router

__all__ = [
    "chat_router",
    "security_router",
    "memory_router",
    "automation_router",
    "selfmod_router",
]
