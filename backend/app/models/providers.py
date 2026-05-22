"""Model provider interface and registry.

Defines ModelProvider ABC, ProviderRegistry for discovering available
providers based on environment credentials, and FastAPI dependency.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from pydantic import BaseModel


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
    """Discovers and manages available model providers based on credentials."""

    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        """Create provider instances for available credentials."""
        qwen_key = os.getenv("QWEN_API_KEY", "")
        if qwen_key:
            from app.models.qwen import QwenProvider

            base_url = os.getenv(
                "QWEN_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            provider = QwenProvider(api_key=qwen_key, base_url=base_url)
            self._providers[provider.model_id] = provider

        local_url = os.getenv("LOCAL_LLM_BASE_URL", "")
        if local_url:
            from app.models.openai_compatible import OpenAICompatibleProvider

            api_key = os.getenv("LOCAL_LLM_API_KEY", "ollama")
            provider = OpenAICompatibleProvider(base_url=local_url, api_key=api_key)
            self._providers[provider.model_id] = provider

    def get_provider(self, model_id: str) -> ModelProvider:
        """Get provider by model_id. Raises KeyError if not found."""
        if model_id not in self._providers:
            raise KeyError(f"Model '{model_id}' not available")
        return self._providers[model_id]

    def get_available_models(self) -> list[dict[str, str]]:
        """Return list of available models with id, name, description."""
        return [
            {
                "id": p.model_id,
                "name": p.display_name,
                "description": p.description,
            }
            for p in self._providers.values()
        ]


def get_provider_registry() -> ProviderRegistry:
    """FastAPI dependency that provides a ProviderRegistry."""
    return ProviderRegistry()
