"""OpenAI-compatible provider — uses openai SDK with custom base_url."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.models.providers import ModelProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(ModelProvider):
    """OpenAI-compatible model provider (local LLMs via Ollama, vLLM, etc.)."""

    provider_id: str = "local-llm"
    display_name: str = "Local LLM"
    description: str = "Local OpenAI-compatible model server"

    def __init__(
        self,
        base_url: str,
        api_key: str = "ollama",
        model_id: str = "local-model",
    ) -> None:
        self.model_id = model_id
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def chat_completion(self, messages: list[dict[str, str]]) -> str:
        """Call OpenAI-compatible chat completions (non-streaming)."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model_id,
                messages=messages,  # type: ignore[arg-type]
                stream=False,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("OpenAI-compatible provider error: %s", e)
            raise
