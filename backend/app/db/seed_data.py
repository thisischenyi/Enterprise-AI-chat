"""Seed data — creates mock test users and seeds model configs from env vars.

Test users:
- employee@test-enterprise.com (role=employee)
- admin@test-enterprise.com (role=admin)

Model configs are seeded from environment variables so the admin dashboard
reflects the currently working providers (Qwen, local LLM).
"""

import asyncio
import os
import uuid

from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.schema import Base, ModelConfig, PolicyConfig, User

EMPLOYEE_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ADMIN_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

TEST_USERS = [
    {
        "id": EMPLOYEE_USER_ID,
        "email": "employee@test-enterprise.com",
        "name": "Test Employee",
        "role": "employee",
    },
    {
        "id": ADMIN_USER_ID,
        "email": "admin@test-enterprise.com",
        "name": "Test Admin",
        "role": "admin",
    },
]


async def seed_users(database_url: str) -> None:
    """Insert mock test users into the database."""
    engine_kwargs = {}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_async_engine(database_url, echo=False, **engine_kwargs)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for user_data in TEST_USERS:
            result = await session.execute(sa_select(User).where(User.email == user_data["email"]))
            existing = result.scalar_one_or_none()
            if existing is None:
                user = User(**user_data)
                session.add(user)

        await session.commit()

    await engine.dispose()


SEED_MODELS = [
    # Qwen: availability = API key, endpoint from separate env var
    {
        "provider_type": "qwen",
        "name": "Qwen (通义千问)",
        "check_env": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],  # at least one must be set
        "api_key_env": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
        "endpoint_env": "QWEN_BASE_URL",
        "endpoint_default": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_id_env": "QWEN_MODEL",
        "model_id_default": "qwen-plus",
    },
    # OpenAI-compatible: availability = endpoint URL, API key has default
    {
        "provider_type": "openai_compatible",
        "name": "Local LLM",
        "check_env": ["LOCAL_LLM_BASE_URL", "OPENAI_API_BASE"],  # at least one must be set
        "api_key_env": ["LOCAL_LLM_API_KEY", "OPENAI_API_KEY"],
        "api_key_default": "ollama",
        "endpoint_env": ["LOCAL_LLM_BASE_URL", "OPENAI_API_BASE"],
        "model_id_env": ["LOCAL_LLM_MODEL_ID", "OPENAI_MODEL_NAME"],
        "model_id_default": "local-model",
    },
]


def _first_env(env_vars: list[str]) -> str | None:
    """Return the value of the first env var that is set, or None."""
    for var in env_vars:
        val = os.getenv(var)
        if val:
            return val
    return None


async def seed_model_configs(database_url: str) -> None:
    """Seed ModelConfig records from environment variables.

    Only creates entries for providers whose availability env var is set.
    Skips if a model_id already exists in the table (idempotent).
    """
    from app.admin.models_repo import encrypt_key

    engine_kwargs = {}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_async_engine(database_url, echo=False, **engine_kwargs)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Only seed if no ModelConfig records exist — admin manages configs after that
        existing = await session.execute(sa_select(ModelConfig))
        if existing.scalars().first() is not None:
            return

        for spec in SEED_MODELS:
            # Check if provider is configured
            if not _first_env(spec["check_env"]):
                continue

            # Get API key
            api_key = _first_env(spec["api_key_env"]) or spec.get("api_key_default", "")
            if not api_key:
                continue

            # Get endpoint URL
            if isinstance(spec["endpoint_env"], list):
                endpoint = _first_env(spec["endpoint_env"])
            else:
                endpoint = os.getenv(spec["endpoint_env"])
            endpoint = endpoint or spec.get("endpoint_default", "")
            if not endpoint:
                continue

            # Get model ID
            if isinstance(spec["model_id_env"], list):
                model_id = _first_env(spec["model_id_env"])
            else:
                model_id = os.getenv(spec["model_id_env"])
            model_id = model_id or spec.get("model_id_default", "")

            # Skip if model_id already exists (idempotent)
            existing = await session.execute(sa_select(ModelConfig).where(ModelConfig.model_id == model_id))
            if existing.scalar_one_or_none() is not None:
                continue

            config = ModelConfig(
                name=spec["name"],
                provider_type=spec["provider_type"],
                endpoint_url=endpoint,
                api_key_encrypted=encrypt_key(api_key),
                model_id=model_id,
                enabled=True,
            )
            session.add(config)

        await session.commit()

    await engine.dispose()


SEED_POLICY_CONFIGS = [
    {"scanner_name": "data_protection", "enabled": True, "sensitivity": "medium"},
    {"scanner_name": "content_guard", "enabled": True, "sensitivity": "medium"},
]


async def seed_policy_configs(database_url: str) -> None:
    """Seed default PolicyConfig records for safety scanners.

    Only creates entries if no PolicyConfig rows exist (idempotent).
    Admin manages configs via /api/admin/policy after initial seed.
    """
    engine_kwargs = {}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_async_engine(database_url, echo=False, **engine_kwargs)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        existing = await session.execute(sa_select(PolicyConfig))
        if existing.scalars().first() is not None:
            await engine.dispose()
            return

        for cfg_data in SEED_POLICY_CONFIGS:
            result = await session.execute(
                sa_select(PolicyConfig).where(PolicyConfig.scanner_name == cfg_data["scanner_name"])
            )
            if result.scalar_one_or_none() is None:
                config = PolicyConfig(**cfg_data)
                session.add(config)

        await session.commit()

    await engine.dispose()


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./enterprise_chat_mvp.db")
    asyncio.run(seed_users(database_url))
    asyncio.run(seed_model_configs(database_url))
    asyncio.run(seed_policy_configs(database_url))


if __name__ == "__main__":
    main()