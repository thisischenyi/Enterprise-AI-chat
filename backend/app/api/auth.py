"""Auth API routes — mock OIDC login, callback, and current user endpoints.

Implements the full mock OIDC flow per D-01 (simulated OIDC with redirect)
and D-02 (role selector on mock login page).
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.current_user import get_current_user
from app.auth.oidc import MockOIDCProvider
from app.db import get_db_session
from app.db.schema import Session, User

router = APIRouter()

mock_oidc = MockOIDCProvider()


@router.post("/login")
async def login(role: str = "employee") -> dict[str, str]:
    """Initiate mock OIDC login flow per D-01.

    Returns redirect_url (frontend mock login page) and signed state_token
    that the frontend passes back on callback.
    """
    if role not in ("employee", "admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}. Must be 'employee' or 'admin'.",
        )
    return mock_oidc.initiate_login(role)


@router.post("/callback")
async def callback(
    role: str = "employee",
    state_token: str = "",
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    """Mock OIDC callback per D-01/D-02.

    Validates signed state_token, creates/finds user in DB,
    creates session row with signed token, sets session cookie,
    returns user identity.
    """
    # Validate state token (per T-01-01: validate mock token signature)
    try:
        user_info = mock_oidc.handle_callback(state_token, role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # Look up or create user in DB
    result = await db.execute(
        select(User).where(User.email == user_info["email"])
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Create user if not exists (first mock login)
        user = User(
            email=user_info["email"],
            name=user_info["name"],
            role=user_info["role"],
        )
        db.add(user)
        await db.flush()

    # Generate session token and create session row in DB (per D-03)
    session_token = user_info["session_token"]
    expires_at = datetime.utcnow() + timedelta(hours=1)

    session_obj = Session(
        user_id=user.id,
        token=session_token,
        expires_at=expires_at,
    )
    db.add(session_obj)
    await db.flush()

    # Build response with session cookie and user identity (per T-01-03)
    response = JSONResponse(
        content={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
        },
        status_code=200,
    )
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        secure=False,  # False for local dev; True in production
        samesite="lax",  # Lax for local dev; Strict in production
        max_age=3600,
    )
    return response


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    """Return current authenticated user identity."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
    }