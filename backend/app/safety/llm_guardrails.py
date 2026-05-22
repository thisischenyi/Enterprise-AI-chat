"""LLM guardrail scanner using ProtectAI LLM Guard.

Detects prompt injection, jailbreak attempts, and harmful/toxic content
using LLM Guard scanners wrapped in asyncio.to_thread().
"""

from __future__ import annotations

import asyncio
import logging

from app.safety.scanner_interface import RiskCategory, ScannerFinding, ScannerResult

logger = logging.getLogger(__name__)

# Mapping from scanner name to RiskCategory
_SCANNER_CATEGORY_MAP = {
    "prompt_injection": RiskCategory.prompt_injection,
    "toxicity": RiskCategory.harmful_content,
}


class LLMGuardrailScanner:
    """LLM Guard-backed safety scanner.

    Implements the Scanner protocol. Uses PromptInjection and Toxicity
    scanners from llm-guard. There is no separate Jailbreak scanner in
    llm-guard 0.3.x -- PromptInjection covers both.
    """

    def __init__(self) -> None:
        # Patch torch.jit before importing llm_guard
        import app.safety.torch_compat  # noqa: F401
        from llm_guard.input_scanners import PromptInjection, Toxicity

        self._scanners = {
            "prompt_injection": PromptInjection(),
            "toxicity": Toxicity(),
        }
        logger.info("LLMGuardrailScanner initialized with scanners: %s", list(self._scanners.keys()))

    async def scan(self, content: str, source: str) -> ScannerResult:
        """Scan content for prompt injection, jailbreak, and harmful content.

        Args:
            content: Text to scan.
            source: "input" or "output".

        Returns:
            ScannerResult with findings mapped to RiskCategory.
        """
        try:
            results = await asyncio.to_thread(self._scan_sync, content)
            findings = self._map_to_findings(results)
            return ScannerResult(
                findings=findings,
                has_violations=len(findings) > 0,
                scanner_name="llm_guardrails",
            )
        except Exception as e:
            logger.warning("LLMGuardrailScanner error: %s", e)
            return ScannerResult(findings=[], has_violations=False, scanner_name="llm_guardrails")

    def _scan_sync(self, content: str) -> dict:
        """Run all scanners synchronously. Called via asyncio.to_thread()."""
        results = {}
        for name, scanner in self._scanners.items():
            try:
                sanitized_output, is_valid, risk_score = scanner.scan(content)
                results[name] = {
                    "is_valid": is_valid,
                    "risk_score": risk_score,
                }
            except Exception as e:
                logger.warning("Scanner '%s' failed: %s", name, e)
        return results

    def _map_to_findings(self, results: dict) -> list[ScannerFinding]:
        """Map scanner results to ScannerFinding instances."""
        findings: list[ScannerFinding] = []

        for name, result in results.items():
            if not result["is_valid"]:
                category = _SCANNER_CATEGORY_MAP.get(name, RiskCategory.harmful_content)
                risk_score = result["risk_score"]

                findings.append(ScannerFinding(
                    category=category,
                    confidence=risk_score,
                    anonymized_detail=f"Detected {name} violation",
                ))

                # PromptInjection also maps to jailbreak at high risk
                if name == "prompt_injection" and risk_score >= 0.9:
                    findings.append(ScannerFinding(
                        category=RiskCategory.jailbreak,
                        confidence=risk_score,
                        anonymized_detail="Detected jailbreak pattern",
                    ))

        return findings
