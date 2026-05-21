"""Enterprise AI Chat MVP — FastAPI application entry point."""

from fastapi import FastAPI

from app.api import auth

app = FastAPI(title="Enterprise AI Chat MVP", version="0.1.0")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}