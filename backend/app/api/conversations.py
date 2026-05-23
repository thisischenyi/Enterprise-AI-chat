"""Conversation API routes — list conversations and fetch messages."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.current_user import get_current_user
from app.db import get_db_session
from app.db.schema import User
from app.conversations.repository import ConversationRepository

router = APIRouter()


# --- Response models ---


class ConversationSummary(BaseModel):
    id: str
    title: str
    model_id: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    extra: dict | None = None
    created_at: str


# --- Endpoints ---


@router.get("")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ConversationSummary]:
    """List conversations for the current user."""
    repo = ConversationRepository(db)
    user_id = uuid.UUID(str(current_user.id))
    conversations = await repo.list_for_user(user_id)
    return [
        ConversationSummary(
            id=str(c.id),
            title=c.title,
            model_id=c.model_id,
            updated_at=c.updated_at.isoformat(),
        )
        for c in conversations
    ]


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    """Delete a conversation and its messages. Returns 403 if user doesn't own it."""
    repo = ConversationRepository(db)
    user_id = uuid.UUID(str(current_user.id))
    conv_uuid = uuid.UUID(conversation_id)

    deleted = await repo.delete_conversation(conv_uuid, user_id)
    if not deleted:
        raise HTTPException(status_code=403, detail="Access denied")
    await db.commit()
    return Response(status_code=204)


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[MessageResponse]:
    """Get messages for a conversation. Returns 403 if user doesn't own it."""
    repo = ConversationRepository(db)
    user_id = uuid.UUID(str(current_user.id))
    conv_uuid = uuid.UUID(conversation_id)

    conversation = await repo.get_conversation(conv_uuid, user_id)
    if conversation is None:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await repo.get_messages(conv_uuid)
    return [
        MessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            extra=m.extra,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]
