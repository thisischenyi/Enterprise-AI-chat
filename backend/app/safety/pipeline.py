"""Safety pipeline — Phase 2 placeholder.

Coordinates input and output safety scanning with fail-closed semantics.
"""


class SafetyPipeline:
    """Phase 2 placeholder — safety pipeline stub."""

    async def scan_input(self, content: str) -> dict[str, str]:
        """Stub: returns placeholder response."""
        return {"action": "allow", "message": "Safety pipeline stub - Phase 2"}

    async def scan_output(self, content: str) -> dict[str, str]:
        """Stub: returns placeholder response."""
        return {"action": "allow", "message": "Safety pipeline stub - Phase 2"}