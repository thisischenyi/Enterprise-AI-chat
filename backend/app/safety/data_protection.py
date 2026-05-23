"""Data protection scanner using Microsoft Presidio.

Detects PII and sensitive data in content using Presidio AnalyzerEngine
with all built-in recognizers plus custom enterprise recognizers.

Note: Presidio's NLP engine is English-only (en_core_web_lg). To avoid
massive false positives on Chinese text where the NLP model misidentifies
normal words as PII entities, we use a high score_threshold (0.7) so
only high-confidence regex-based matches (emails, phone numbers, SSNs,
credit cards, etc.) trigger findings. Context-boosted low-confidence
NLP guesses are filtered out.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re

from app.safety.scanner_interface import RiskCategory, ScannerFinding, ScannerResult

logger = logging.getLogger(__name__)

# Entity type to RiskCategory mapping
_ENTITY_CATEGORY_MAP: dict[str, RiskCategory] = {
    # PII entities — only high-confidence regex matches
    "EMAIL_ADDRESS": RiskCategory.pii,
    "PHONE_NUMBER": RiskCategory.pii,
    "US_SSN": RiskCategory.pii,
    "CREDIT_CARD": RiskCategory.pii,
    "IBAN_CODE": RiskCategory.pii,
    "IP_ADDRESS": RiskCategory.pii,
    "US_DRIVER_LICENSE": RiskCategory.pii,
    "US_PASSPORT": RiskCategory.pii,
    "CHINESE_NATIONAL_ID": RiskCategory.pii,
    "INCOME": RiskCategory.pii,
    # Sensitive data entities (enterprise-specific)
    "EMPLOYEE_ID": RiskCategory.sensitive_data,
    "PROJECT_CODE": RiskCategory.sensitive_data,
}

# Entity types to IGNORE — these rely on English NLP context which causes
# false positives on Chinese/mixed-language text (e.g. "泰山" → LOCATION)
_NLP_ENTITIES_TO_IGNORE = {
    "PERSON", "LOCATION", "DATE_TIME", "NRP", "AGE", "ORGANIZATION", "ID",
    "MEDICAL_LICENSE", "URL", "US_BANK_NUMBER", "UK_NHS", "MAC_ADDRESS",
    "CRYPTO", "US_ITIN",
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
            IncomeRecognizer,
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

        # Remove NLP-dependent recognizers that cause false positives on Chinese text.
        # Walk recognizers list directly — get_recognizers() throws if no match.
        to_remove = [
            rec for rec in self._analyzer.registry.recognizers
            if set(rec.supported_entities) & _NLP_ENTITIES_TO_IGNORE
        ]
        for rec in to_remove:
            self._analyzer.registry.remove_recognizer(rec.name)

        # Register custom recognizers
        self._analyzer.registry.add_recognizer(EmployeeIdRecognizer())
        self._analyzer.registry.add_recognizer(ProjectCodeRecognizer())
        self._analyzer.registry.add_recognizer(ChineseNationalIdRecognizer())
        self._analyzer.registry.add_recognizer(IncomeRecognizer())

        # Only scan entities that have reliable regex-based detection
        self._scan_entities = list(_ENTITY_CATEGORY_MAP.keys())

        logger.info(
            "DataProtectionScanner initialized: model=%s, entities=%s",
            spacy_model, self._scan_entities,
        )

    async def scan(self, content: str, source: str) -> ScannerResult:
        """Scan content for PII and sensitive data.

        Only scans high-confidence regex-matchable entity types.
        NLP-dependent entities (PERSON, LOCATION, etc.) are excluded
        to prevent false positives on non-English text.
        """
        try:
            analyzer_results = await asyncio.to_thread(
                self._analyzer.analyze,
                text=content,
                language="en",
                entities=self._scan_entities,
                score_threshold=0.7,
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
                logger.info(
                    "PII found: entity=%s, score=%.2f, text=%r",
                    result.entity_type, result.score,
                    content[result.start:result.end],
                )

            if not findings:
                logger.info("No PII found in content: %r", content[:100])

            return ScannerResult(
                findings=findings,
                has_violations=len(findings) > 0,
                scanner_name="data_protection",
            )
        except Exception as e:
            logger.warning("DataProtectionScanner error: %s", e)
            return ScannerResult(findings=[], has_violations=False, scanner_name="data_protection")
