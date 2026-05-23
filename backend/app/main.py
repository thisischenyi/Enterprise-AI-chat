"""Enterprise AI Chat MVP — FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api import admin, auth, chat, chat_stream, conversations
from app.db import init_db

# Load APIKEY.env from project root (two levels up from this file's package)
_project_root = Path(__file__).parent.parent.parent
load_dotenv(_project_root / "APIKEY.env", override=True)

# Configure logging — INFO level so safety scan details appear in console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


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
app.include_router(chat_stream.router, prefix="/api/chat", tags=["chat-stream"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}