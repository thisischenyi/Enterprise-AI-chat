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
from app.db import get_db_session
from app.db.schema import User
from app.audit.repository import AuditRepository
from app.models.providers import ProviderRegistry, get_provider_registry
from app.safety.pipeline import SafetyPipeline
from app.safety.policy import SafetyPolicy
from app.safety.scanner_interface import PolicyDecision

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Request/Response models ---


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    model_id: str


class ChatResponse(BaseModel):
    status: Literal["allowed", "blocked", "fail_closed"]
    content: str
    model_id: str | None = None
    provider_id: str | None = None
    risk_categories: list[str] | None = None
    revision_hint: str | None = None


class ModelInfo(BaseModel):
    id: str
    name: str
    description: str


# --- Dependencies ---


def get_safety_pipeline() -> SafetyPipeline:
    """Create SafetyPipeline with no scanners for MVP (scanners added when deps available)."""
    policy = SafetyPolicy()
    return SafetyPipeline(scanners=[], policy=policy, timeout=30.0)


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

    # Validate model_id exists in registry
    try:
        provider = registry.get_provider(request.model_id)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Model '{request.model_id}' not available")

    # Step 1: Input safety scan
    input_decision = await pipeline.scan_input(request.message, user_id, request.model_id)

    if input_decision.action == "block":
        await audit_repo.record_event(user_id, request.model_id, "input", input_decision)
        return ChatResponse(
            status="blocked",
            content=input_decision.block_message or "Your message was blocked.",
            risk_categories=input_decision.risk_categories,
            revision_hint="Please revise your message to avoid sensitive content.",
        )

    if input_decision.action == "fail_closed":
        await audit_repo.record_event(user_id, request.model_id, "input", input_decision)
        return ChatResponse(
            status="fail_closed",
            content=input_decision.block_message or "Your message could not be processed due to a system error. Please try again later.",
        )

    # Step 2: Call model provider
    try:
        messages = [{"role": "user", "content": request.message}]
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
        )

    if output_decision.action == "fail_closed":
        await audit_repo.record_event(user_id, request.model_id, "output", output_decision)
        return ChatResponse(
            status="fail_closed",
            content=output_decision.block_message or "Your message could not be processed due to a system error. Please try again later.",
        )

    # Step 4: Allowed — record audit and return response
    await audit_repo.record_event(user_id, request.model_id, "output", output_decision)
    return ChatResponse(
        status="allowed",
        content=model_response,
        model_id=provider.model_id,
        provider_id=provider.provider_id,
    )


@router.get("/models")
async def chat_models(
    current_user: User = Depends(get_current_user),
    registry: ProviderRegistry = Depends(get_provider_registry),
) -> list[ModelInfo]:
    """Return available model providers with valid credentials."""
    models = registry.get_available_models()
    return [ModelInfo(id=m["id"], name=m["name"], description=m["description"]) for m in models]
