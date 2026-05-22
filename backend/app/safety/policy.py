"""Safety policy — evaluates aggregated scanner findings into decisions.

Any violation results in full content block (no partial display).
Block messages use category-specific templates without echoing content.
"""

from __future__ import annotations

from app.safety.block_messages import FAIL_CLOSED_MESSAGE, get_block_message
from app.safety.scanner_interface import (
    PolicyDecision,
    RiskCategory,
    ScannerResult,
)


class SafetyPolicy:
    """Evaluates aggregated scanner findings into allow/block/fail_closed decisions."""

    def evaluate(self, results: list[ScannerResult], source: str) -> PolicyDecision:
        """Aggregate findings from all scanners into a single policy decision.

        Args:
            results: List of ScannerResult from all scanners.
            source: "input" or "output".

        Returns:
            PolicyDecision with action, block_message, and anonymized metadata.
        """
        all_findings = []
        for result in results:
            if result.has_violations:
                all_findings.extend(result.findings)

        if not all_findings:
            return PolicyDecision(
                action="allow",
                risk_categories=[],
                block_message=None,
                scanner_findings_summary={},
            )

        # Collect unique risk categories
        categories: list[RiskCategory] = []
        for finding in all_findings:
            if finding.category not in categories:
                categories.append(finding.category)

        # Generate block message from templates (never echoes content)
        block_message = get_block_message(categories, source)

        # Build anonymized findings summary (metadata only per SAFE-06)
        scanner_findings_summary = {
            "scanners": list({r.scanner_name for r in results if r.has_violations}),
            "categories": [c.value for c in categories],
            "finding_count": len(all_findings),
            "findings": [
                {
                    "category": f.category.value,
                    "confidence": f.confidence,
                    "detail": f.anonymized_detail,
                }
                for f in all_findings
            ],
        }

        return PolicyDecision(
            action="block",
            risk_categories=[c.value for c in categories],
            block_message=block_message,
            scanner_findings_summary=scanner_findings_summary,
        )
