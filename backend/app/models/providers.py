"""Model provider interface — Phase 2 placeholder.

Defines the abstract provider interface that QwenProvider and
OpenAICompatibleProvider will implement in future phases.
"""


class ModelProvider:
    """Phase 2 placeholder — model provider interface stub."""

    provider_id: str = ""
    model_id: str = ""

    async def chat_completion(self, messages: list[dict[str, str]]) -> dict[str, str]:
        """Stub: returns placeholder response."""
        return {"message": "Model provider stub - Phase 2"}