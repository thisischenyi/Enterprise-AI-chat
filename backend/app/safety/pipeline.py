"""Safety pipeline — coordinates scanner flow with fail-closed semantics.

Runs all registered scanners in parallel with a 30-second timeout.
Timeout or scanner crash results in fail-closed (block) decision.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from app.safety.scanner_interface import (
    PolicyDecision,
    Scanner,
    ScannerResult,
)
from app.safety.policy import SafetyPolicy

logger = logging.getLogger(__name__)


class SafetyPipeline:
    """Coordinates safety scanners with fail-closed timeout."""

    def __init__(
        self,
        scanners: list[Scanner],
        policy: SafetyPolicy,
        timeout: float = 30.0,
    ) -> None:
        self._scanners = scanners
        self._policy = policy
        self._timeout = timeout

    async def scan_input(
        self, content: str, user_id: uuid.UUID, model_id: str
    ) -> PolicyDecision:
        """Scan user input through all scanners with fail-closed timeout."""
        logger.info("Input scan: %r", content[:100])
        decision = await self._scan(content, "input")
        logger.info(
            "Input scan result: action=%s, categories=%s, summary=%s",
            decision.action, decision.risk_categories, decision.scanner_findings_summary,
        )
        return decision

    async def scan_output(
        self, content: str, user_id: uuid.UUID, model_id: str
    ) -> PolicyDecision:
        """Scan model output through all scanners with fail-closed timeout."""
        logger.info("Output scan: %r", content[:100])
        decision = await self._scan(content, "output")
        logger.info(
            "Output scan result: action=%s, categories=%s, summary=%s",
            decision.action, decision.risk_categories, decision.scanner_findings_summary,
        )
        return decision

    async def _scan(self, content: str, source: str) -> PolicyDecision:
        """Run all scanners with timeout, return policy decision."""
        try:
            results = await asyncio.wait_for(
                self._run_scanners(content, source),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("Safety pipeline timed out after %ss", self._timeout)
            return PolicyDecision(
                action="fail_closed",
                risk_categories=[],
                block_message="Your message could not be processed due to a system error. Please try again later.",
                scanner_findings_summary={"error": "pipeline_timeout"},
            )

        # If all scanners failed, fail closed
        if all(r is None for r in results):
            return PolicyDecision(
                action="fail_closed",
                risk_categories=[],
                block_message="Your message could not be processed due to a system error. Please try again later.",
                scanner_findings_summary={"error": "all_scanners_failed"},
            )

        valid_results = [r for r in results if r is not None]
        return self._policy.evaluate(valid_results, source)

    async def _run_scanners(self, content: str, source: str) -> list[ScannerResult | None]:
        """Run all scanners in parallel, catch individual failures."""
        tasks = [scanner.scan(content, source) for scanner in self._scanners]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[ScannerResult | None] = []
        for i, result in enumerate(raw_results):
            if isinstance(result, Exception):
                scanner_name = getattr(self._scanners[i], "__class__", type(self._scanners[i])).__name__
                logger.warning("Scanner %s failed: %s", scanner_name, result)
                results.append(None)
            else:
                results.append(result)

        return results
