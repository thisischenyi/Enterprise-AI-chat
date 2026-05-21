"""OpenAI-compatible provider — Phase 2 placeholder.

Will implement local LLM calls via OpenAI SDK with custom base_url.
"""


class OpenAICompatibleProvider:
    """Phase 2 placeholder — OpenAI-compatible provider stub."""

    async def chat_completion(self, messages: list[dict[str, str]]) -> dict[str, str]:
        """Stub: returns placeholder response."""
        return {"message": "OpenAI-compatible provider stub - Phase 2"}