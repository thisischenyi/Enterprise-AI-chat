"""Model configuration repository — CRUD with encrypted API key storage."""

import os
import uuid as uuid_mod
from base64 import urlsafe_b64encode, urlsafe_b64decode

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import ModelConfig


def _get_fernet() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        # MVP fallback: derive a key from SECRET_KEY
        secret = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
        # Fernet requires 32 url-safe base64 bytes
        padded = secret.ljust(32, "0")[:32]
        key = urlsafe_b64encode(padded.encode()).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def mask_key(encrypted_key: str) -> str:
    """Return masked display: last 4 chars of decrypted key."""
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_key.encode()).decode()
        last4 = decrypted[-4:] if len(decrypted) >= 4 else decrypted
        return f"••••{last4}"
    except Exception:
        return "••••****"


def encrypt_key(raw_key: str) -> str:
    fernet = _get_fernet()
    return fernet.encrypt(raw_key.encode()).decode()


def decrypt_key(encrypted_key: str) -> str:
    """Decrypt an API key from the database for actual use."""
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_key.encode()).decode()


class ModelConfigRepository:
    @staticmethod
    async def list_models(session: AsyncSession) -> list[ModelConfig]:
        result = await session.execute(select(ModelConfig))
        return list(result.scalars().all())

    @staticmethod
    async def get_model(session: AsyncSession, model_id: uuid_mod.UUID) -> ModelConfig | None:
        result = await session.execute(
            select(ModelConfig).where(ModelConfig.id == model_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_model(session: AsyncSession, data: dict) -> ModelConfig:
        model = ModelConfig(
            name=data["name"],
            provider_type=data["provider_type"],
            endpoint_url=data["endpoint_url"],
            api_key_encrypted=encrypt_key(data["api_key"]),
            model_id=data["model_id"],
            enabled=data.get("enabled", True),
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)
        return model

    @staticmethod
    async def update_model(session: AsyncSession, model_id: uuid_mod.UUID, data: dict) -> ModelConfig | None:
        model = await ModelConfigRepository.get_model(session, model_id)
        if not model:
            return None
        if "name" in data:
            model.name = data["name"]
        if "provider_type" in data:
            model.provider_type = data["provider_type"]
        if "endpoint_url" in data:
            model.endpoint_url = data["endpoint_url"]
        if "model_id" in data:
            model.model_id = data["model_id"]
        if "enabled" in data:
            model.enabled = data["enabled"]
        # D-ADM11: if api_key is empty/None, keep existing
        if data.get("api_key"):
            model.api_key_encrypted = encrypt_key(data["api_key"])
        await session.commit()
        await session.refresh(model)
        return model

    @staticmethod
    async def delete_model(session: AsyncSession, model_id: uuid_mod.UUID) -> bool:
        model = await ModelConfigRepository.get_model(session, model_id)
        if not model:
            return False
        await session.delete(model)
        await session.commit()
        return True
