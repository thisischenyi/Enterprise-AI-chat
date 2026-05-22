"""Custom Presidio recognizers for enterprise PII detection.

Three recognizers for enterprise-specific PII:
- EmployeeIdRecognizer: EMP-XXXX pattern with NLP context
- ProjectCodeRecognizer: PRJ-XXXX pattern with NLP context
- ChineseNationalIdRecognizer: 18-digit ID with checksum validation
"""

from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult


class EmployeeIdRecognizer(PatternRecognizer):
    """Detects employee IDs in EMP-XXXX format with NLP context words."""

    PATTERNS = [
        Pattern(
            name="employee_id",
            regex=r"EMP-\d{4}",
            score=0.5,
        ),
    ]

    CONTEXT = [
        "employee",
        "id",
        "staff",
        "number",
        "雇员",
        "编号",
    ]

    SUPPORTED_LANGUAGE = "en"

    def __init__(self, name: str = "EmployeeIdRecognizer", **kwargs):
        super().__init__(
            name=name,
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=self.SUPPORTED_LANGUAGE,
            **kwargs,
        )


class ProjectCodeRecognizer(PatternRecognizer):
    """Detects project codes in PRJ-XXXX format with NLP context words."""

    PATTERNS = [
        Pattern(
            name="project_code",
            regex=r"PRJ-[A-Z0-9]{4}",
            score=0.5,
        ),
    ]

    CONTEXT = [
        "project",
        "code",
        "program",
        "项目",
    ]

    SUPPORTED_LANGUAGE = "en"

    def __init__(self, name: str = "ProjectCodeRecognizer", **kwargs):
        super().__init__(
            name=name,
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=self.SUPPORTED_LANGUAGE,
            **kwargs,
        )


# Checksum table for Chinese national ID validation
_CHECKSUM_TABLE = [1, 0, "X", 9, 8, 7, 6, 5, 4, 3, 2]
_WEIGHT_FACTORS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]


def _validate_chinese_national_id_checksum(id_number: str) -> bool:
    """Validate Chinese national ID checksum.

    Computes weighted sum of first 17 digits mod 11, then maps to checksum table.
    """
    try:
        digits = [int(d) for d in id_number[:17]]
        weighted_sum = sum(d * w for d, w in zip(digits, _WEIGHT_FACTORS))
        remainder = weighted_sum % 11
        expected_last = _CHECKSUM_TABLE[remainder]
        actual_last = id_number[17].upper()
        if expected_last == "X":
            return actual_last == "X"
        return actual_last == str(expected_last)
    except (ValueError, IndexError):
        return False


class ChineseNationalIdRecognizer(PatternRecognizer):
    """Detects Chinese national IDs (18-digit) with checksum validation.

    Uses regex to find candidates, then validates checksum.
    Confidence is HIGH with checksum match + context, LOW if checksum fails.
    """

    PATTERNS = [
        Pattern(
            name="chinese_national_id",
            regex=r"\d{17}[\dXx]",
            score=0.3,  # Base score — boosted by checksum and context
        ),
    ]

    CONTEXT = [
        "身份证",
        "身份证号码",
        "身份証",
        "身份证号",
        "ID card",
    ]

    SUPPORTED_LANGUAGE = "zh"

    def __init__(self, name: str = "ChineseNationalIdRecognizer", **kwargs):
        super().__init__(
            name=name,
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=self.SUPPORTED_LANGUAGE,
            **kwargs,
        )

    def analyze(self, text: str, entities: list[str] | None = None, nlp_artifacts=None) -> list[RecognizerResult]:
        """Override analyze to add checksum validation and adjust confidence."""
        results = super().analyze(text, entities, nlp_artifacts)

        validated_results = []
        for result in results:
            candidate = text[result.start:result.end]
            if _validate_chinese_national_id_checksum(candidate):
                result.score = 0.85  # High confidence — checksum valid
            else:
                result.score = 0.01  # Checksum failed — likely random digits

            if result.score >= 0.1:
                validated_results.append(result)

        return validated_results