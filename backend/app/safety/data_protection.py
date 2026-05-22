"""Data protection scanner using Microsoft Presidio.

Detects PII and sensitive data in content using Presidio AnalyzerEngine
with all built-in recognizers plus custom enterprise recognizers.
"""

from __future__ import annotations

import asyncio
import logging
import os

from app.safety.scanner_interface import RiskCategory, ScannerFinding, ScannerResult

logger = logging.getLogger(__name__)

# Entity type to RiskCategory mapping
_ENTITY_CATEGORY_MAP: dict[str, RiskCategory] = {
    # PII entities
    "PERSON": RiskCategory.pii,
    "EMAIL_ADDRESS": RiskCategory.pii,
    "PHONE_NUMBER": RiskCategory.pii,
    "US_SSN": RiskCategory.pii,
    "CREDIT_CARD": RiskCategory.pii,
    "IBAN_CODE": RiskCategory.pii,
    "IP_ADDRESS": RiskCategory.pii,
    "US_DRIVER_LICENSE": RiskCategory.pii,
    "US_PASSPORT": RiskCategory.pii,
    "LOCATION": RiskCategory.pii,
    "DATE_TIME": RiskCategory.pii,
    "NRP": RiskCategory.pii,
    "MEDICAL_LICENSE": RiskCategory.pii,
    "URL": RiskCategory.pii,
    "CHINESE_NATIONAL_ID": RiskCategory.pii,
    # Sensitive data entities (enterprise-specific)
    "EMPLOYEE_ID": RiskCategory.sensitive_data,
    "PROJECT_CODE": RiskCategory.sensitive_data,
}


class DataProtectionScanner:
    """Presidio-backed PII and sensitive data scanner.

    Implements the Scanner protocol. Wraps Presidio AnalyzerEngine
    in asyncio.to_thread() for async compatibility.
    """

    def __init__(self) -> None:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        from app.safety.custom_recognizers import (
            ChineseNationalIdRecognizer,
            EmployeeIdRecognizer,
            ProjectCodeRecognizer,
        )

        spacy_model = os.environ.get("SPACY_MODEL", "en_core_web_lg")

        # Configure NLP engine with spaCy
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": spacy_model},
            ],
        }
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()

        self._analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=["en"],
        )

        # Register custom recognizers
        self._analyzer.registry.add_recognizer(EmployeeIdRecognizer())
        self._analyzer.registry.add_recognizer(ProjectCodeRecognizer())
        self._analyzer.registry.add_recognizer(ChineseNationalIdRecognizer())

        logger.info("DataProtectionScanner initialized with spaCy model: %s", spacy_model)

    async def scan(self, content: str, source: str) -> ScannerResult:
        """Scan content for PII and sensitive data.

        Args:
            content: Text to scan.
            source: "input" or "output".

        Returns:
            ScannerResult with findings mapped to RiskCategory.
        """
        try:
            analyzer_results = await asyncio.to_thread(
                self._analyzer.analyze,
                text=content,
                language="en",
                entities=None,
            )

            findings: list[ScannerFinding] = []
            for result in analyzer_results:
                category = _ENTITY_CATEGORY_MAP.get(result.entity_type, RiskCategory.pii)
                finding = ScannerFinding(
                    category=category,
                    confidence=result.score,
                    anonymized_detail=f"Detected {result.entity_type} pattern",
                )
                findings.append(finding)

            return ScannerResult(
                findings=findings,
                has_violations=len(findings) > 0,
                scanner_name="data_protection",
            )
        except Exception as e:
            logger.warning("DataProtectionScanner error: %s", e)
            return ScannerResult(findings=[], has_violations=False, scanner_name="data_protection")
