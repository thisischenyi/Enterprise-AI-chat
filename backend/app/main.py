"""Enterprise AI Chat MVP — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import admin, auth, chat, conversations
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables and seed mock users."""
    await init_db()
    yield


app = FastAPI(title="Enterprise AI Chat MVP", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}