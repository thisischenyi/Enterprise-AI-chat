"""Admin API routes — admin-only endpoints with role enforcement.

Admin endpoints require Depends(get_admin_user) which checks user.role == "admin"
and raises 403 for non-admin users (per AUTH-03 and threat model T-01-04, T-01-10).
403 response contains only generic "Admin access required" message — no user
identity or role enumeration hints (per T-01-10).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.audit_queries import (
    AuditStats,
    list_audit_events,
    get_audit_stats,
)
from app.admin.models_repo import ModelConfigRepository, mask_key
from app.admin.policy_repo import PolicyConfigRepository
from app.audit.events import AuditEventResponse
from app.auth.current_user import get_admin_user
from app.db import get_db_session
from app.db.schema import User

router = APIRouter()


class PaginatedAuditResponse(BaseModel):
    events: list[AuditEventResponse]
    total: int
    page: int
    page_size: int


@router.get("/config")
async def admin_config(current_user: User = Depends(get_admin_user)) -> dict[str, str]:
    """Admin configuration endpoint — Phase 4 placeholder.

    Only accessible to admin-role users. Returns role confirmation.
    Employee and unauthenticated users receive 403/401 respectively.
    """
    return {
        "message": "Admin configuration endpoint - Phase 4",
        "user_role": current_user.role,
    }


@router.get("/audit", response_model=PaginatedAuditResponse)
async def get_audit_events(
    time_range: str = Query("today", pattern="^(today|7d|30d)$"),
    user_id: str | None = Query(None),
    model_id: str | None = Query(None),
    action: str | None = Query(None),
    risk_category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> PaginatedAuditResponse:
    """Paginated audit events with multi-dimension filters."""
    events, total = await list_audit_events(
        session=db,
        time_range=time_range,
        user_id=user_id,
        model_id=model_id,
        action=action,
        risk_category=risk_category,
        page=page,
        page_size=page_size,
    )
    return PaginatedAuditResponse(
        events=[AuditEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/audit/stats", response_model=AuditStats)
async def get_audit_statistics(
    time_range: str = Query("today", pattern="^(today|7d|30d)$"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> AuditStats:
    """Audit statistics for dashboard cards."""
    return await get_audit_stats(session=db, time_range=time_range)


# --- Model Config Schemas ---

class CreateModelRequest(BaseModel):
    name: str = Field(max_length=100)
    provider_type: str = Field(pattern="^(qwen|openai_compatible)$")
    endpoint_url: str = Field(max_length=500)
    model_id: str = Field(max_length=100)
    api_key: str = Field(min_length=1)
    enabled: bool = True


class UpdateModelRequest(BaseModel):
    name: str | None = Field(None, max_length=100)
    provider_type: str | None = Field(None, pattern="^(qwen|openai_compatible)$")
    endpoint_url: str | None = Field(None, max_length=500)
    model_id: str | None = Field(None, max_length=100)
    api_key: str | None = None
    enabled: bool | None = None


class ModelConfigResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    endpoint_url: str
    model_id: str
    api_key_masked: str
    enabled: bool
    created_at: str


# --- Model Config Endpoints ---

@router.get("/models")
async def list_models(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ModelConfigResponse]:
    models = await ModelConfigRepository.list_models(db)
    return [
        ModelConfigResponse(
            id=str(m.id),
            name=m.name,
            provider_type=m.provider_type,
            endpoint_url=m.endpoint_url,
            model_id=m.model_id,
            api_key_masked=mask_key(m.api_key_encrypted),
            enabled=m.enabled,
            created_at=m.created_at.isoformat(),
        )
        for m in models
    ]


@router.post("/models", status_code=201)
async def create_model(
    data: CreateModelRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> ModelConfigResponse:
    model = await ModelConfigRepository.create_model(db, data.model_dump())
    return ModelConfigResponse(
        id=str(model.id),
        name=model.name,
        provider_type=model.provider_type,
        endpoint_url=model.endpoint_url,
        model_id=model.model_id,
        api_key_masked=mask_key(model.api_key_encrypted),
        enabled=model.enabled,
        created_at=model.created_at.isoformat(),
    )


@router.put("/models/{model_id}")
async def update_model(
    model_id: uuid.UUID,
    data: UpdateModelRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> ModelConfigResponse:
    model = await ModelConfigRepository.update_model(
        db, model_id, data.model_dump(exclude_unset=True)
    )
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelConfigResponse(
        id=str(model.id),
        name=model.name,
        provider_type=model.provider_type,
        endpoint_url=model.endpoint_url,
        model_id=model.model_id,
        api_key_masked=mask_key(model.api_key_encrypted),
        enabled=model.enabled,
        created_at=model.created_at.isoformat(),
    )


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    deleted = await ModelConfigRepository.delete_model(db, model_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Model not found")


# --- Policy Config Schemas ---

class PolicyConfigResponse(BaseModel):
    scanner_name: str
    enabled: bool
    sensitivity: str


class UpdatePolicyRequest(BaseModel):
    enabled: bool
    sensitivity: str = Field(pattern="^(low|medium|high)$")


# --- Policy Config Endpoints ---

@router.get("/policy")
async def list_policies(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[PolicyConfigResponse]:
    policies = await PolicyConfigRepository.list_policies(db)
    return [
        PolicyConfigResponse(
            scanner_name=p.scanner_name,
            enabled=p.enabled,
            sensitivity=p.sensitivity,
        )
        for p in policies
    ]


@router.put("/policy/{scanner_name}")
async def update_policy(
    scanner_name: str,
    data: UpdatePolicyRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session),
) -> PolicyConfigResponse:
    policy = await PolicyConfigRepository.update_policy(
        db, scanner_name, data.enabled, data.sensitivity
    )
    if not policy:
        raise HTTPException(status_code=404, detail="Scanner not found")
    return PolicyConfigResponse(
        scanner_name=policy.scanner_name,
        enabled=policy.enabled,
        sensitivity=policy.sensitivity,
    )
