"""Current user dependency — FastAPI Depends for authenticated user identity.

Extracts user from session cookie via DB lookup. Session tokens are
signed with itsdangerous and stored in DB (SQLite for MVP, per D-03).
Invalid/expired sessions return 401 (fail-closed, per threat model T-01-02).
"""

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.db.schema import Session, User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Extract authenticated user from session cookie via DB lookup.

    1. Extract session_id from cookie named "session_id"
    2. Query session table in DB for matching token
    3. Verify session has not expired
    4. Return the associated User object

    Raises HTTPException 401 if session missing, expired, or invalid.
    """
    session_token = request.cookies.get("session_id")
    if session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Query session by token
    result = await db.execute(
        select(Session).where(Session.token == session_token)
    )
    session_obj = result.scalar_one_or_none()

    if session_obj is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    # Check session expiry (fail-closed per T-01-02)
    # Compare as naive UTC — SQLite strips timezone info on read,
    # PostgreSQL stores timezone-aware. Handle both by comparing naive UTC.
    now_utc = datetime.utcnow()
    expires_at_naive = session_obj.expires_at
    if expires_at_naive.tzinfo is not None:
        expires_at_naive = expires_at_naive.replace(tzinfo=None)
    if expires_at_naive < now_utc:
        await db.delete(session_obj)
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )

    # Load the associated user
    result = await db.execute(
        select(User).where(User.id == session_obj.user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify current user has admin role (per AUTH-03 and T-01-04).

    Returns User if role is 'admin', raises 403 otherwise.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user