"""Scanner interface types for the safety pipeline.

Defines the Scanner protocol, result types, finding types,
policy decision types, risk category enum, and scanner config.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Protocol


class RiskCategory(Enum):
    """Risk categories for safety scanner findings."""

    pii = "pii"
    sensitive_data = "sensitive_data"
    prompt_injection = "prompt_injection"
    jailbreak = "jailbreak"
    harmful_content = "harmful_content"
    compliance = "compliance"


@dataclass
class ScannerFinding:
    """A single finding from a safety scanner.

    anonymized_detail contains type labels only (e.g. "Detected SSN pattern"),
    never raw detected content values.
    """

    category: RiskCategory
    confidence: float
    anonymized_detail: str


@dataclass
class ScannerConfig:
    """Configuration for a safety scanner — driven by PolicyConfig DB table.

    Maps admin-facing sensitivity (low/medium/high) to concrete scanner params:
    - score_threshold: minimum confidence for DataProtectionScanner findings
    - min_confidence: minimum rule confidence for ContentGuardScanner regex rules
    """

    enabled: bool = True
    score_threshold: float = 0.7
    min_confidence: float = 0.80


@dataclass
class ScannerResult:
    """Result from a safety scanner scan operation."""

    findings: list[ScannerFinding] = field(default_factory=list)
    has_violations: bool = False
    scanner_name: str = ""


@dataclass
class PolicyDecision:
    """Decision from the safety policy evaluator.

    block_message contains category-specific template text (never echoes content).
    scanner_findings_summary contains anonymized metadata only.
    """

    action: Literal["allow", "block", "fail_closed"]
    risk_categories: list[str] = field(default_factory=list)
    block_message: str | None = None
    scanner_findings_summary: dict = field(default_factory=dict)


class Scanner(Protocol):
    """Protocol for safety scanner implementations."""

    async def scan(self, content: str, source: Literal["input", "output"]) -> ScannerResult:
        """Scan content and return findings.

        Args:
            content: The text to scan for safety violations.
            source: Whether this is an input (user message) or output (model response) scan.

        Returns:
            ScannerResult with findings list and violation flag.
        """
        ...