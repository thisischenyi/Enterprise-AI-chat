"""Database module — async SQLAlchemy engine and session factory.

Uses SQLite (aiosqlite) for MVP development. Production can switch
to PostgreSQL (asyncpg) by changing DATABASE_URL in .env.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./enterprise_chat_mvp.db")

# SQLite-specific engine args: check_same_thread=False for async compatibility
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(DATABASE_URL, echo=False, **engine_kwargs)

# SQLite pragmas for concurrent access: WAL mode + busy_timeout
# WAL mode allows concurrent reads while one writer holds the lock.
# busy_timeout=30000ms gives other writers 30s to wait for lock release
# (SSE streams can hold connections for extended periods).
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

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
    """Create all tables and seed mock users + model configs on startup."""
    from app.db.schema import Base
    from app.db.seed_data import seed_users, seed_model_configs, seed_policy_configs

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await seed_users(DATABASE_URL)
    await seed_model_configs(DATABASE_URL)
    await seed_policy_configs(DATABASE_URL)