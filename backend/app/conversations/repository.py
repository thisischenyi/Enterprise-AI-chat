"""Conversation repository — CRUD operations for conversations and messages."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import Conversation, Message


class ConversationRepository:
    """Manages conversation and message persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_conversation(
        self, user_id: uuid.UUID, title: str, model_id: str
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            model_id=model_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def list_for_user(self, user_id: uuid.UUID) -> list[Conversation]:
        """List conversations for a user, ordered by updated_at desc."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation | None:
        """Get a conversation, filtered by user ownership."""
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_message(
        self, conversation_id: uuid.UUID, role: str, content: str, extra: dict | None = None
    ) -> Message:
        """Add a message to a conversation."""
        message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            extra=extra,
            created_at=datetime.utcnow(),
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def get_messages(self, conversation_id: uuid.UUID) -> list[Message]:
        """Get all messages for a conversation, ordered by created_at asc."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_timestamp(self, conversation_id: uuid.UUID) -> None:
        """Update conversation's updated_at to now."""
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=datetime.utcnow())
        )
        await self._session.execute(stmt)
