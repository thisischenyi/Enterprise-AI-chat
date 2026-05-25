"""Chat API routes — POST /send and GET /models with safety pipeline integration.

Chat endpoints require authenticated user. POST /send runs safety pipeline
(input scan -> model call -> output scan) and records audit events for every decision.
"""

from __future__ import annotations

import logging
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.current_user import get_current_user
from app.admin.policy_repo import PolicyConfigRepository
from app.db import get_db_session
from app.db.schema import User
from app.audit.repository import AuditRepository
from app.conversations.repository import ConversationRepository
from app.models.providers import ProviderRegistry, get_provider_registry
from app.safety.pipeline import SafetyPipeline
from app.safety.policy import SafetyPolicy
from app.safety.scanner_interface import PolicyDecision, ScannerConfig

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Request/Response models ---


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    model_id: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    status: Literal["allowed", "blocked", "fail_closed"]
    content: str
    model_id: str | None = None
    provider_id: str | None = None
    risk_categories: list[str] | None = None
    revision_hint: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str


# --- Dependencies ---


SENSITIVITY_MAP: dict[str, dict[str, float]] = {
    "low": {"data_protection": 0.5, "content_guard": 0.95},
    "medium": {"data_protection": 0.7, "content_guard": 0.80},
    "high": {"data_protection": 0.85, "content_guard": 0.70},
}

DEFAULT_SCANNER_CONFIGS: dict[str, ScannerConfig] = {
    "data_protection": ScannerConfig(enabled=True, score_threshold=0.7, min_confidence=0.80),
    "content_guard": ScannerConfig(enabled=True, score_threshold=0.7, min_confidence=0.80),
}


async def get_safety_pipeline(db: AsyncSession = Depends(get_db_session)) -> SafetyPipeline:
    """Create SafetyPipeline driven by PolicyConfig from DB.

    Reads scanner enabled/sensitivity from the policy_configs table.
    Disabled scanners are excluded. Sensitivity maps to concrete thresholds
    via SENSITIVITY_MAP. Falls back to defaults if DB has no config rows.
    """
    try:
        policies = await PolicyConfigRepository.list_policies(db)
    except Exception as e:
        logger.warning("Failed to read PolicyConfig from DB, using defaults: %s", e)
        policies = []

    configs: dict[str, ScannerConfig] = {}
    for p in policies:
        thresholds = SENSITIVITY_MAP.get(p.sensitivity, SENSITIVITY_MAP["medium"])
        thresholds_for_scanner = thresholds.get(p.scanner_name, SENSITIVITY_MAP["medium"][p.scanner_name] if p.scanner_name in SENSITIVITY_MAP["medium"] else 0.7)
        configs[p.scanner_name] = ScannerConfig(
            enabled=p.enabled,
            score_threshold=thresholds_for_scanner,
            min_confidence=thresholds_for_scanner,
        )

    # Fill in defaults for any scanner not in DB
    for name, default in DEFAULT_SCANNER_CONFIGS.items():
        if name not in configs:
            configs[name] = default

    scanners = []

    dp_config = configs.get("data_protection", DEFAULT_SCANNER_CONFIGS["data_protection"])
    if dp_config.enabled:
        try:
            from app.safety.data_protection import DataProtectionScanner
            scanners.append(DataProtectionScanner(score_threshold=dp_config.score_threshold))
            logger.info("DataProtectionScanner enabled: score_threshold=%.2f", dp_config.score_threshold)
        except Exception as e:
            logger.warning("DataProtectionScanner unavailable: %s", e)

    cg_config = configs.get("content_guard", DEFAULT_SCANNER_CONFIGS["content_guard"])
    if cg_config.enabled:
        try:
            import app.safety.torch_compat  # noqa: F401 — must patch before transformers
            from app.safety.llm_guardrails import LLMGuardrailScanner
            scanners.append(LLMGuardrailScanner(min_confidence=cg_config.min_confidence))
            logger.info("ContentGuardScanner enabled: min_confidence=%.2f", cg_config.min_confidence)
        except Exception as e:
            logger.warning("ContentGuardScanner unavailable: %s", e)

    if not scanners:
        logger.warning("No scanners enabled — pipeline will always allow unless fail-closed triggers")

    logger.info("SafetyPipeline initialized with %d scanner(s)", len(scanners))
    policy = SafetyPolicy()
    return SafetyPipeline(scanners=scanners, policy=policy, timeout=30.0)


# --- Endpoints ---


@router.post("/send")
async def chat_send(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    pipeline: SafetyPipeline = Depends(get_safety_pipeline),
    registry: ProviderRegistry = Depends(get_provider_registry),
    db: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    """Send a chat message through safety pipeline -> model -> output scan."""
    user_id = uuid.UUID(str(current_user.id))
    audit_repo = AuditRepository(db)
    conv_repo = ConversationRepository(db)

    # Validate model_id exists in registry
    try:
        provider = registry.get_provider(request.model_id)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Model '{request.model_id}' not available")

    # Load existing conversation and history if conversation_id provided
    conversation = None
    history_messages: list[dict[str, str]] = []
    if request.conversation_id:
        conv_uuid = uuid.UUID(request.conversation_id)
        conversation = await conv_repo.get_conversation(conv_uuid, user_id)
        if conversation is None:
            raise HTTPException(status_code=403, detail="Access denied")
        # Load last 20 messages as context — exclude blocked roles
        all_messages = await conv_repo.get_messages(conv_uuid)
        history_messages = []
        for m in all_messages[-20:]:
            if m.role == "blocked":
                continue
            role = m.role if m.role in ("system", "user", "assistant", "tool") else "user"
            history_messages.append({"role": role, "content": m.content})

    # Lazy-create conversation if needed (before input scan so we can store blocked messages)
    if conversation is None:
        title = request.message[:50]
        conversation = await conv_repo.create_conversation(user_id, title, request.model_id)

    # Build messages list for model call
    messages = history_messages + [{"role": "user", "content": request.message}]

    # Step 1: Input safety scan
    input_decision = await pipeline.scan_input(request.message, user_id, request.model_id)

    if input_decision.action == "block":
        await audit_repo.record_event(user_id, request.model_id, "input", input_decision)
        
        # Store user message and blocked message in conversation
        await conv_repo.add_message(conversation.id, "user", request.message)
        block_message = input_decision.block_message or "Your message was blocked."
        blocked_msg = await conv_repo.add_message(
            conversation.id,
            "blocked",
            block_message,
            extra={"risk_categories": input_decision.risk_categories},
        )
        await conv_repo.update_timestamp(conversation.id)
        
        return ChatResponse(
            status="blocked",
            content=block_message,
            risk_categories=input_decision.risk_categories,
            revision_hint="Please revise your message to avoid sensitive content.",
            conversation_id=str(conversation.id),
            message_id=str(blocked_msg.id),
        )

    if input_decision.action == "fail_closed":
        await audit_repo.record_event(user_id, request.model_id, "input", input_decision)
        
        # Store user message and blocked message in conversation
        await conv_repo.add_message(conversation.id, "user", request.message)
        block_message = input_decision.block_message or "Your message could not be processed due to a system error. Please try again later."
        blocked_msg = await conv_repo.add_message(
            conversation.id,
            "blocked",
            block_message,
            extra={"risk_categories": [], "error": "fail_closed"},
        )
        await conv_repo.update_timestamp(conversation.id)
        
        return ChatResponse(
            status="fail_closed",
            content=block_message,
            conversation_id=str(conversation.id),
            message_id=str(blocked_msg.id),
        )

    # Store user message
    user_msg = await conv_repo.add_message(conversation.id, "user", request.message)

    # Step 2: Call model provider
    try:
        model_response = await provider.chat_completion(messages)
    except Exception as e:
        logger.error("Model provider error: %s", e)
        error_decision = PolicyDecision(
            action="fail_closed",
            risk_categories=[],
            block_message="Your message could not be processed due to a system error. Please try again later.",
            scanner_findings_summary={"error": "model_provider_error"},
        )
        await audit_repo.record_event(user_id, request.model_id, "output", error_decision)
        return ChatResponse(
            status="fail_closed",
            content=error_decision.block_message or "",
            conversation_id=str(conversation.id),
        )

    # Step 3: Output safety scan
    output_decision = await pipeline.scan_output(model_response, user_id, request.model_id)

    if output_decision.action == "block":
        await audit_repo.record_event(user_id, request.model_id, "output", output_decision)
        return ChatResponse(
            status="blocked",
            content=output_decision.block_message or "The model response was blocked.",
            risk_categories=output_decision.risk_categories,
            revision_hint="The model response contained content that violates safety policies.",
            conversation_id=str(conversation.id),
        )

    if output_decision.action == "fail_closed":
        await audit_repo.record_event(user_id, request.model_id, "output", output_decision)
        return ChatResponse(
            status="fail_closed",
            content=output_decision.block_message or "Your message could not be processed due to a system error. Please try again later.",
            conversation_id=str(conversation.id),
        )

    # Step 4: Allowed — store assistant message, update timestamp, audit, return
    assistant_msg = await conv_repo.add_message(conversation.id, "assistant", model_response)
    await conv_repo.update_timestamp(conversation.id)
    await audit_repo.record_event(user_id, request.model_id, "output", output_decision)
    return ChatResponse(
        status="allowed",
        content=model_response,
        model_id=provider.model_id,
        provider_id=provider.provider_id,
        conversation_id=str(conversation.id),
        message_id=str(assistant_msg.id),
    )


@router.get("/models")
async def chat_models(
    current_user: User = Depends(get_current_user),
    registry: ProviderRegistry = Depends(get_provider_registry),
) -> list[ModelInfo]:
    """Return available model providers with valid credentials."""
    models = registry.get_available_models()
    return [ModelInfo(id=m["id"], name=m["name"], description=m["description"]) for m in models]
