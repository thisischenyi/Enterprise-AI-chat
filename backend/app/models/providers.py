"""Model provider interface and registry.

ProviderRegistry reads from the ModelConfig database table (admin-managed)
and falls back to environment variables only if DB is empty. Admin config
changes (enable/disable, API key, endpoint) take effect immediately on
the next request — no restart needed.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.db.schema import ModelConfig

logger = logging.getLogger(__name__)


class ModelProvider(ABC):
    """Abstract base for model providers."""

    provider_id: str
    model_id: str
    display_name: str
    description: str

    @abstractmethod
    async def chat_completion(self, messages: list[dict[str, str]]) -> str:
        """Send messages and return model response content text."""
        ...


class ModelResponse(BaseModel):
    """Internal model response representation."""

    content: str
    model_id: str
    provider_id: str


class ProviderRegistry:
    """Manages available model providers. DB-first, env-var fallback."""

    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {}
        # DB-provided display names override provider class defaults
        self._display_names: dict[str, str] = {}

    async def init_from_db(self, db: AsyncSession) -> None:
        """Load enabled model configs from database, decrypt API keys."""
        from app.admin.models_repo import decrypt_key

        result = await db.execute(
            select(ModelConfig).where(ModelConfig.enabled == True)
        )
        configs = list(result.scalars().all())

        for cfg in configs:
            try:
                api_key = decrypt_key(cfg.api_key_encrypted)
            except Exception:
                logger.warning("Failed to decrypt API key for %s, skipping", cfg.model_id)
                continue

            provider = _create_provider(
                provider_type=cfg.provider_type,
                name=cfg.name,
                endpoint_url=cfg.endpoint_url,
                api_key=api_key,
                model_id=cfg.model_id,
            )
            if provider:
                self._providers[provider.model_id] = provider
                self._display_names[provider.model_id] = cfg.name
                logger.info("Loaded model from DB: %s (%s)", cfg.model_id, cfg.name)

        if not self._providers:
            logger.info("No enabled models in DB, falling back to env vars")
            self._init_from_env()

    def _init_from_env(self) -> None:
        """Fallback: create provider instances from environment variables."""
        qwen_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY", "")
        if qwen_key:
            from app.models.qwen import QwenProvider

            base_url = os.getenv(
                "QWEN_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            model_id = os.getenv("QWEN_MODEL", "qwen-plus")
            provider = QwenProvider(api_key=qwen_key, base_url=base_url, model_id=model_id)
            self._providers[provider.model_id] = provider

        openai_url = os.getenv("OPENAI_API_BASE") or os.getenv("LOCAL_LLM_BASE_URL", "")
        if openai_url:
            from app.models.openai_compatible import OpenAICompatibleProvider

            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LOCAL_LLM_API_KEY", "ollama")
            model_id = os.getenv("OPENAI_MODEL_NAME") or os.getenv("LOCAL_LLM_MODEL_ID", "local-model")
            provider = OpenAICompatibleProvider(base_url=openai_url, api_key=api_key, model_id=model_id)
            self._providers[provider.model_id] = provider

    def get_provider(self, model_id: str) -> ModelProvider:
        """Get provider by model_id. Raises KeyError if not found."""
        if model_id not in self._providers:
            raise KeyError(f"Model '{model_id}' not available")
        return self._providers[model_id]

    def get_available_models(self) -> list[dict[str, str]]:
        """Return list of available models with id, name, description.

        Uses DB-provided display names when available (from admin config),
        falls back to provider class defaults otherwise.
        """
        return [
            {
                "id": p.model_id,
                "name": self._display_names.get(p.model_id, p.display_name),
                "description": p.description,
            }
            for p in self._providers.values()
        ]


def _create_provider(
    provider_type: str,
    name: str,
    endpoint_url: str,
    api_key: str,
    model_id: str,
) -> ModelProvider | None:
    """Create a ModelProvider instance from config params."""
    if provider_type == "qwen":
        from app.models.qwen import QwenProvider
        return QwenProvider(api_key=api_key, base_url=endpoint_url, model_id=model_id)
    if provider_type == "openai_compatible":
        from app.models.openai_compatible import OpenAICompatibleProvider
        return OpenAICompatibleProvider(base_url=endpoint_url, api_key=api_key, model_id=model_id)
    logger.warning("Unknown provider_type: %s", provider_type)
    return None


async def get_provider_registry(db: AsyncSession = Depends(get_db_session)) -> ProviderRegistry:
    """FastAPI dependency — loads models from DB, env-var fallback if empty."""
    registry = ProviderRegistry()
    await registry.init_from_db(db)
    return registry