"""StreamingChatService — orchestrates buffer + safety scan + SSE event generation."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditRepository
from app.conversations.repository import ConversationRepository
from app.models.providers import ProviderRegistry
from app.safety.pipeline import SafetyPipeline
from app.safety.scanner_interface import PolicyDecision
from app.streaming.buffer import SentenceBuffer

logger = logging.getLogger(__name__)

# Redaction labels by risk category
REDACTION_LABELS: dict[str, str] = {
    "pii": "[PII已过滤]",
    "secrets": "[机密信息已过滤]",
    "default": "[策略违规已过滤]",
}


def _get_redaction_label(risk_categories: list[str]) -> str:
    """Return appropriate Chinese redaction label for risk category."""
    for cat in risk_categories:
        cat_lower = cat.lower()
        if "pii" in cat_lower or "personal" in cat_lower:
            return REDACTION_LABELS["pii"]
        if "secret" in cat_lower or "credential" in cat_lower:
            return REDACTION_LABELS["secrets"]
    return REDACTION_LABELS["default"]


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
        """Yield SSE event dicts: chunk, redacted, done, error."""
        audit_repo = AuditRepository(db)
        conv_repo = ConversationRepository(db)
        had_redactions = False

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

        # Build messages for model
        all_messages = await conv_repo.get_messages(conversation.id)
        history = [{"role": m.role, "content": m.content} for m in all_messages[-20:]]

        # Step 2: Call model with streaming
        buffer = SentenceBuffer()
        try:
            # Use non-streaming call and simulate token delivery
            # (providers don't yet support stream=True; deliver full response through buffer)
            model_response = await provider.chat_completion(history)
        except Exception as e:
            logger.error("Model provider error during stream: %s", e)
            yield {"event": "error", "data": {"message": "模型服务异常"}}
            return

        # Feed full response through buffer for sentence-level safety scanning
        sentences = buffer.add_token(model_response)
        final_chunk = buffer.flush()
        if final_chunk:
            sentences.append(final_chunk)

        # Step 3: Scan each sentence and emit events
        for sentence in sentences:
            decision = await pipeline.scan_output(sentence, user_id, model_id)
            if decision.action == "allow":
                yield {"event": "chunk", "data": {"content": sentence}}
            else:
                had_redactions = True
                label = _get_redaction_label(decision.risk_categories)
                yield {
                    "event": "redacted",
                    "data": {
                        "category": decision.risk_categories[0] if decision.risk_categories else "policy",
                        "label": label,
                    },
                }

        # Step 4: Store full (unredacted) response in DB
        assistant_msg = await conv_repo.add_message(
            conversation.id, "assistant", buffer.full_response
        )
        await conv_repo.update_timestamp(conversation.id)

        # Audit
        overall_action = "partial_redact" if had_redactions else "allow"
        audit_decision = PolicyDecision(
            action=overall_action,
            risk_categories=[],
            block_message=None,
            scanner_findings_summary={"streaming": True, "redacted": had_redactions},
        )
        await audit_repo.record_event(user_id, model_id, "output", audit_decision)

        # Done event
        yield {
            "event": "done",
            "data": {
                "conversation_id": str(conversation.id),
                "message_id": str(assistant_msg.id),
            },
        }
