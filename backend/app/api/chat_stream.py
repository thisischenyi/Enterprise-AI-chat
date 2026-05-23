"""Streaming chat endpoint — POST /api/chat/stream returning SSE events."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.auth.current_user import get_current_user
from app.db import async_session_factory
from app.db.schema import User
from app.api.chat import get_safety_pipeline
from app.models.providers import ProviderRegistry, get_provider_registry
from app.safety.pipeline import SafetyPipeline
from app.streaming.service import StreamingChatService

router = APIRouter()


class ChatStreamRequest(BaseModel):
    message: str = Field(min_length=1)
    model_id: str
    conversation_id: str | None = None


async def _event_generator(
    request: ChatStreamRequest,
    user_id: uuid.UUID,
    pipeline: SafetyPipeline,
    registry: ProviderRegistry,
):
    """Wrap StreamingChatService as SSE event dicts for EventSourceResponse.

    Manages DB session manually because SSE responses hold injected sessions
    for the entire connection duration, blocking concurrent SQLite writes.
    Uses asyncio.shield on cleanup so client disconnect doesn't leak sessions.
    """
    session = async_session_factory()
    try:
        service = StreamingChatService()
        async for event in service.stream_response(
            message=request.message,
            model_id=request.model_id,
            conversation_id=request.conversation_id,
            user_id=user_id,
            db=session,
            pipeline=pipeline,
            registry=registry,
        ):
            yield {"event": event["event"], "data": json.dumps(event["data"])}
        # service.stream_response commits at each write boundary, so no
        # final commit needed — avoids holding the SQLite write lock.
    except Exception:
        try:
            await asyncio.shield(session.rollback())
        except asyncio.CancelledError:
            pass
        raise
    finally:
        try:
            await asyncio.shield(session.close())
        except asyncio.CancelledError:
            await session.close()


@router.post("/stream")
async def chat_stream(
    request: ChatStreamRequest,
    current_user: User = Depends(get_current_user),
    pipeline: SafetyPipeline = Depends(get_safety_pipeline),
    registry: ProviderRegistry = Depends(get_provider_registry),
) -> EventSourceResponse:
    """Stream chat response with sentence-buffered safety scanning."""
    user_id = uuid.UUID(str(current_user.id))
    return EventSourceResponse(
        _event_generator(request, user_id, pipeline, registry)
    )