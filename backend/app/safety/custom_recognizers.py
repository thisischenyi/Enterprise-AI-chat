"""Custom Presidio recognizers for enterprise PII detection.

Four recognizers for enterprise-specific PII:
- EmployeeIdRecognizer: EMP-XXXX pattern with NLP context
- ProjectCodeRecognizer: PRJ-XXXX pattern with NLP context
- ChineseNationalIdRecognizer: 18-digit ID with checksum validation
- IncomeRecognizer: salary/income amounts near salary keywords
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
            supported_entity="EMPLOYEE_ID",
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
            supported_entity="PROJECT_CODE",
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

    SUPPORTED_LANGUAGE = "en"  # Must match the language we pass to analyzer (currently always "en")

    def __init__(self, name: str = "ChineseNationalIdRecognizer", **kwargs):
        super().__init__(
            supported_entity="CHINESE_NATIONAL_ID",
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


# Salary/income keywords in Chinese and English
_SALARY_KEYWORDS = [
    "工资", "薪资", "薪酬", "薪水", "月薪", "年薪", "收入",
    "salary", "income", "pay", "wage", "compensation", "earnings",
]


class IncomeRecognizer(PatternRecognizer):
    """Detects salary/income amounts near salary keywords.

    Matches numbers (3+ digits) when salary-related keywords appear
    within 60 characters of the number. This catches inputs like
    "我的工资是23133" where "23133" alone wouldn't be recognized as PII.
    """

    PATTERNS = [
        Pattern(
            name="income_amount",
            regex=r"\b\d{3,12}\b",
            score=0.4,
        ),
    ]

    CONTEXT = _SALARY_KEYWORDS

    SUPPORTED_LANGUAGE = "en"

    def __init__(self, name: str = "IncomeRecognizer", **kwargs):
        super().__init__(
            supported_entity="INCOME",
            name=name,
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language=self.SUPPORTED_LANGUAGE,
            **kwargs,
        )

    def analyze(self, text: str, entities: list[str] | None = None, nlp_artifacts=None) -> list[RecognizerResult]:
        """Override to boost confidence when salary keywords are nearby."""
        results = super().analyze(text, entities, nlp_artifacts)

        text_lower = text.lower()
        has_salary_context = any(kw in text_lower for kw in _SALARY_KEYWORDS)

        if not has_salary_context:
            # No salary keywords in the whole text — these are just random numbers
            return []

        # Salary context exists — boost confidence for nearby numbers
        validated = []
        for result in results:
            # Check if a salary keyword is within 60 chars of this number
            start = max(0, result.start - 60)
            end = min(len(text), result.end + 60)
            surrounding = text[start:end].lower()
            if any(kw in surrounding for kw in _SALARY_KEYWORDS):
                result.score = 0.85  # High confidence — number + salary keyword
                validated.append(result)

        return validated