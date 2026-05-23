"""StreamingChatService — orchestrates buffer + safety scan + SSE event generation.

Per project spec: "Block full content on any policy violation — no redaction
or partial display." If any sentence in the model output has a violation,
the ENTIRE output is blocked with a category-specific message. Clean output
is streamed sentence-by-sentence.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditRepository
from app.conversations.repository import ConversationRepository
from app.models.providers import ProviderRegistry
from app.safety.block_messages import get_block_message
from app.safety.pipeline import SafetyPipeline
from app.safety.scanner_interface import PolicyDecision, RiskCategory
from app.streaming.buffer import SentenceBuffer

logger = logging.getLogger(__name__)


class StreamingChatService:
    """Streams model response with sentence-buffered safety scanning."""

    async def stream_response(
        self,
        message: str,
        model_id: str,
        conversation_id: str | None,
        user_id: uuid.UUID,
        db: AsyncSession,
        pipeline: SafetyPipeline,
        registry: ProviderRegistry,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Yield SSE event dicts: chunk, blocked, done, error.

        Commits after each DB write phase so SQLite write lock is never held
        between SSE yields — concurrent requests can write unimpeded.
        """
        audit_repo = AuditRepository(db)
        conv_repo = ConversationRepository(db)

        # Validate model
        try:
            provider = registry.get_provider(model_id)
        except KeyError:
            yield {"event": "error", "data": {"message": f"模型 '{model_id}' 不可用"}}
            return

        # Step 1: Input safety scan
        input_decision = await pipeline.scan_input(message, user_id, model_id)
        if input_decision.action in ("block", "fail_closed"):
            await audit_repo.record_event(user_id, model_id, "input", input_decision)
            await db.commit()
            yield {
                "event": "error",
                "data": {"message": input_decision.block_message or "输入内容被安全策略拦截"},
            }
            return

        # Lazy-create or load conversation
        conversation = None
        if conversation_id:
            conv_uuid = uuid.UUID(conversation_id)
            conversation = await conv_repo.get_conversation(conv_uuid, user_id)

        if conversation is None:
            title = message[:50]
            conversation = await conv_repo.create_conversation(user_id, title, model_id)

        # Store user message
        await conv_repo.add_message(conversation.id, "user", message)
        await db.commit()

        # Build messages for model — exclude blocked messages and map roles
        all_messages = await conv_repo.get_messages(conversation.id)
        history = []
        for m in all_messages[-20:]:
            role = m.role
            # Skip blocked messages entirely — they carry block notices, not model context
            if role == "blocked":
                continue
            # Map stored roles to valid OpenAI Chat API roles
            if role not in ("system", "user", "assistant", "tool"):
                role = "user"
            history.append({"role": role, "content": m.content})

        # Step 2: Call model
        buffer = SentenceBuffer()
        try:
            model_response = await provider.chat_completion(history)
            logger.info("Model response: %r", model_response[:200])
        except Exception as e:
            logger.error("Model provider error during stream: %s", e)
            yield {"event": "error", "data": {"message": "模型服务异常"}}
            return

        # Feed full response through buffer for sentence-level safety scanning
        sentences = buffer.add_token(model_response)
        final_chunk = buffer.flush()
        if final_chunk:
            sentences.append(final_chunk)

        # Step 3: Scan all sentences first, then decide: allow all or block all
        sentences_with_decisions = []
        output_violations = []
        for sentence in sentences:
            decision = await pipeline.scan_output(sentence, user_id, model_id)
            sentences_with_decisions.append((sentence, decision))
            if decision.action != "allow":
                output_violations.append(decision)

        if output_violations:
            # Block entire output per spec: no partial display
            all_risk_categories: list[RiskCategory] = []
            for decision in output_violations:
                for rc in decision.risk_categories:
                    cat = RiskCategory(rc) if isinstance(rc, str) else rc
                    if cat not in all_risk_categories:
                        all_risk_categories.append(cat)

            block_message = get_block_message(all_risk_categories, "output")

            # Record audit event for blocked output
            audit_decision = PolicyDecision(
                action="block",
                risk_categories=[c.value for c in all_risk_categories],
                block_message=block_message,
                scanner_findings_summary={
                    "streaming": True,
                    "output_blocked": True,
                    "violation_count": len(output_violations),
                },
            )
            await audit_repo.record_event(user_id, model_id, "output", audit_decision)

            # Store blocked message in conversation (NOT raw model output)
            blocked_msg = await conv_repo.add_message(
                conversation.id,
                "blocked",
                block_message,
                extra={"risk_categories": [c.value for c in all_risk_categories]},
            )
            await conv_repo.update_timestamp(conversation.id)
            await db.commit()

            yield {
                "event": "blocked",
                "data": {
                    "message": block_message,
                    "categories": [c.value for c in all_risk_categories],
                    "conversation_id": str(conversation.id),
                    "message_id": str(blocked_msg.id),
                },
            }
            return

        # All sentences clean — stream them
        for sentence, decision in sentences_with_decisions:
            yield {"event": "chunk", "data": {"content": sentence}}

        # Step 4: Store allowed response in DB
        assistant_msg = await conv_repo.add_message(
            conversation.id, "assistant", buffer.full_response
        )
        await conv_repo.update_timestamp(conversation.id)
        await db.commit()

        # Step 5: Record output audit event
        audit_decision = PolicyDecision(
            action="allow",
            risk_categories=[],
            block_message=None,
            scanner_findings_summary={"streaming": True, "redacted": False},
        )
        await audit_repo.record_event(user_id, model_id, "output", audit_decision)
        await db.commit()

        # Done event — no write lock held at this point
        yield {
            "event": "done",
            "data": {
                "conversation_id": str(conversation.id),
                "message_id": str(assistant_msg.id),
            },
        }