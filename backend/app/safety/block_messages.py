"""Block message templates for the safety pipeline.

Category-specific templates for input and output block messages.
Templates never echo detected content — only category labels and revision hints.
"""

from __future__ import annotations

from app.safety.scanner_interface import RiskCategory

# Each entry: (RiskCategory, source) -> (template_text, revision_hint)
BLOCK_MESSAGE_TEMPLATES: dict[tuple[RiskCategory, str], tuple[str, str]] = {
    # PII / Sensitive Data
    (RiskCategory.pii, "input"): (
        "Your message was blocked because it contains personal or sensitive information.",
        "Please remove any personal details and try again.",
    ),
    (RiskCategory.pii, "output"): (
        "The response was blocked because it contains personal or sensitive information.",
        "Please try a different query.",
    ),
    (RiskCategory.sensitive_data, "input"): (
        "Your message was blocked because it contains sensitive enterprise data.",
        "Please remove any sensitive identifiers and try again.",
    ),
    (RiskCategory.sensitive_data, "output"): (
        "The response was blocked because it contains sensitive enterprise data.",
        "Please try a different query.",
    ),
    # Prompt Injection
    (RiskCategory.prompt_injection, "input"): (
        "Your message was blocked because it appears to contain instructions intended to override system behavior.",
        "Please rephrase your message naturally.",
    ),
    (RiskCategory.prompt_injection, "output"): (
        "The response was blocked because it appears to contain manipulative instructions.",
        "Please try a different query.",
    ),
    # Jailbreak
    (RiskCategory.jailbreak, "input"): (
        "Your message was blocked because it appears to be an attempt to bypass safety constraints.",
        "Please rephrase your message.",
    ),
    (RiskCategory.jailbreak, "output"): (
        "The response was blocked because it appears to contain jailbreak content.",
        "Please try a different query.",
    ),
    # Harmful Content
    (RiskCategory.harmful_content, "input"): (
        "Your message was blocked because it contains harmful or offensive content.",
        "Please rephrase without harmful language.",
    ),
    (RiskCategory.harmful_content, "output"): (
        "The response was blocked because it contains harmful or offensive content.",
        "Please try a different query.",
    ),
    # Compliance
    (RiskCategory.compliance, "input"): (
        "Your message was blocked because it may violate enterprise compliance policies.",
        "Please consult your organization's guidelines.",
    ),
    (RiskCategory.compliance, "output"): (
        "The response was blocked because it may violate compliance policies.",
        "Please try a different query.",
    ),
}

# Severity ordering for combining multiple categories into one message
_SEVERITY_ORDER: list[RiskCategory] = [
    RiskCategory.jailbreak,
    RiskCategory.prompt_injection,
    RiskCategory.harmful_content,
    RiskCategory.pii,
    RiskCategory.sensitive_data,
    RiskCategory.compliance,
]

FAIL_CLOSED_MESSAGE = "Your message could not be processed due to a system error. Please try again later."


def get_block_message(categories: list[RiskCategory], source: str) -> str:
    """Combine risk categories into a single user-facing block message.

    Uses the highest-severity category template, appends revision hint,
    and never concatenates raw detected text.

    Args:
        categories: List of RiskCategory values detected in the content.
        source: "input" or "output" — determines wording.

    Returns:
        A formatted block message string.
    """
    if not categories:
        return FAIL_CLOSED_MESSAGE

    # Find the highest-severity category
    highest = categories[0]
    for severity_cat in _SEVERITY_ORDER:
        if severity_cat in categories:
            highest = severity_cat
            break

    key = (highest, source)
    template, hint = BLOCK_MESSAGE_TEMPLATES.get(key, ("Your message was blocked.", ""))

    if hint:
        return f"{template} {hint}"
    return template