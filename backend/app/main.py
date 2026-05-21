"""Enterprise AI Chat MVP — FastAPI application entry point."""

from fastapi import FastAPI

from app.api import admin, auth, chat

app = FastAPI(title="Enterprise AI Chat MVP", version="0.1.0")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}