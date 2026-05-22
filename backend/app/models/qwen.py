"""Alibaba Bailian Qwen provider — httpx async client with retry."""

from __future__ import annotations

import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.models.providers import ModelProvider

logger = logging.getLogger(__name__)


class QwenProvider(ModelProvider):
    """Qwen model provider using httpx AsyncClient."""

    provider_id: str = "qwen"
    display_name: str = "Alibaba Qwen Max"
    description: str = "Alibaba Cloud Qwen large language model via Bailian API"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_id: str = "qwen-max",
    ) -> None:
        self.model_id = model_id
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def chat_completion(self, messages: list[dict[str, str]]) -> str:
        """Call Qwen chat completions API (non-streaming)."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "stream": False,
                },
            )

            if response.status_code == 429:
                raise httpx.TimeoutException("Rate limited (429)")

            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
