from routes.auth import router as auth_router
from routes.chats import router as chats_router
from routes.health import router as health_router

__all__ = [
    "auth_router",
    "chats_router",
    "health_router",
]
