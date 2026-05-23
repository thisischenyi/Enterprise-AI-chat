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
        "您的消息因包含个人或敏感信息而被拦截。",
        "请移除个人敏感信息后重试。",
    ),
    (RiskCategory.pii, "output"): (
        "回复因包含个人或敏感信息而被拦截。",
        "请尝试其他问题。",
    ),
    (RiskCategory.sensitive_data, "input"): (
        "您的消息因包含企业敏感数据而被拦截。",
        "请移除敏感标识后重试。",
    ),
    (RiskCategory.sensitive_data, "output"): (
        "回复因包含企业敏感数据而被拦截。",
        "请尝试其他问题。",
    ),
    # Prompt Injection
    (RiskCategory.prompt_injection, "input"): (
        "您的消息因疑似包含指令注入而被拦截。",
        "请用自然语言重新表述。",
    ),
    (RiskCategory.prompt_injection, "output"): (
        "回复因疑似包含操控指令而被拦截。",
        "请尝试其他问题。",
    ),
    # Jailbreak
    (RiskCategory.jailbreak, "input"): (
        "您的消息因疑似绕过安全约束而被拦截。",
        "请重新表述您的消息。",
    ),
    (RiskCategory.jailbreak, "output"): (
        "回复因包含越狱内容而被拦截。",
        "请尝试其他问题。",
    ),
    # Harmful Content
    (RiskCategory.harmful_content, "input"): (
        "您的消息因包含有害或不当内容而被拦截。",
        "请移除不当内容后重试。",
    ),
    (RiskCategory.harmful_content, "output"): (
        "回复因包含有害或不当内容而被拦截。",
        "请尝试其他问题。",
    ),
    # Compliance
    (RiskCategory.compliance, "input"): (
        "您的消息因可能违反合规政策而被拦截。",
        "请参考组织合规指南。",
    ),
    (RiskCategory.compliance, "output"): (
        "回复因可能违反合规政策而被拦截。",
        "请尝试其他问题。",
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

FAIL_CLOSED_MESSAGE = "系统处理异常，请稍后重试。"


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