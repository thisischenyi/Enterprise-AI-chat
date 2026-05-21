"""Database module — async SQLAlchemy engine and session factory.

Uses SQLite (aiosqlite) for MVP development. Production can switch
to PostgreSQL (asyncpg) by changing DATABASE_URL in .env.
"""

import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./enterprise_chat_mvp.db")

# SQLite-specific engine args: check_same_thread=False for async compatibility
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(DATABASE_URL, echo=False, **engine_kwargs)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    """FastAPI dependency that yields an async DB session."""
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db() -> None:
    """Create all tables and seed mock users on startup."""
    from app.db.schema import Base
    from app.db.seed_data import seed_users

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await seed_users(DATABASE_URL)