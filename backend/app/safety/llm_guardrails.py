"""Content guard scanner — rule-based injection + harmful content + Qwen3Guard model.

Uses regex rules for prompt injection/jailbreak detection and harmful content
request detection (deterministic, zero false positives on normal text). The
Qwen3Guard-Gen-0.6B generative model provides probabilistic detection for
content the rules don't cover — it generates structured safe/unsafe + category
responses and works well on both Chinese and English text.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re

from app.safety.scanner_interface import RiskCategory, ScannerFinding, ScannerResult

logger = logging.getLogger(__name__)

# --- Rule-based injection patterns ---
# Each rule: (regex_pattern, confidence_score)

_INJECTION_RULES: list[tuple[str, float]] = [
    # --- Instruction override (English) ---
    (r"\b(?:ignore|disregard|forget|override|skip)\b.{0,30}\b(?:instructions|rules|constraints|guidelines|prompt|directions|policy|restrictions)\b", 0.90),
    (r"\bdo\s+not\b.{0,20}\b(?:follow|obey|comply|adhere)\b.{0,20}\b(?:instructions|rules|guidelines|policy)\b", 0.90),
    (r"\b(?:new|different|alternative|updated)\s+instructions\b", 0.85),
    (r"\b(?:new|different|alternative)\s+rules\b", 0.80),

    # --- Identity manipulation (English) ---
    (r"\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as|simulate\s+being|play\s+the\s+role\s+of)\b", 0.85),
    (r"\b(?:from\s+now\s+on|starting\s+now|effective\s+immediately)\b.{0,15}\b(?:you\s+are|respond\s+as|act\s+as)\b", 0.85),

    # --- Safety bypass (English) ---
    (r"\b(?:bypass|circumvent|evade|disable|deactivate|turn\s+off|remove)\b.{0,25}\b(?:safety|security|filter|guard|check|restriction|constraint|policy|protection)\b", 0.95),
    (r"\b(?:no\s+need|don'?t\s+need|without)\b.{0,15}\b(?:safety|security|filter|guard|check|restriction)\b", 0.80),

    # --- System/internal access (English) ---
    (r"\b(?:reveal|disclose|show|tell|give|output|print|display|expose)\b.{0,20}\b(?:system|internal|hidden|secret|confidential|backend|underlying)\b.{0,20}\b(?:prompt|instructions|rules|code|config|key|password|credentials)\b", 0.90),
    (r"\bsystem\s+prompt\b", 0.80),
    (r"\b(?:admin|developer|root|sudo)\b.{0,15}\b(?:mode|access|override|command|console|shell|prompt)\b", 0.90),

    # --- Instruction override (Chinese) ---
    (r"(?:忽略|忘记|无视|不理|跳过).{0,15}(?:指令|规则|约束|指示|提示|限制|安全|过滤)", 0.90),
    (r"覆盖.{0,10}(?:指令|规则|约束|指示|提示|安全)", 0.85),
    (r"新(?:的)?(?:指令|规则|指示)", 0.80),

    # --- Identity manipulation (Chinese) ---
    (r"假装(?:是|为|成|当)", 0.85),
    (r"角色(?:扮演|扮演为|扮演成)", 0.85),
    (r"你(?:现在|从此|即刻|马上)(?:是|成为|当)", 0.85),
    (r"从现在起你(?:是|成为|当)", 0.85),

    # --- Safety bypass (Chinese) ---
    (r"(?:绕过|避开|逃避|关闭|禁用|停用|取消|解除|去掉).{0,15}(?:安全|过滤|检测|审查|防护|限制|约束|保护|验证)", 0.95),

    # --- System/internal access (Chinese) ---
    (r"(?:透露|泄露|揭示|显示|告诉|输出|给出|打印|暴露).{0,15}(?:系统|内部|隐藏|秘密|后台|底层|核心).{0,15}(?:提示|指令|规则|配置|密钥|密码|代码|凭据)", 0.90),
    (r"系统提示", 0.80),
    (r"(?:管理员|开发者|超级|根).{0,10}(?:模式|权限|指令|控制|终端|命令|提示)", 0.90),
]

# --- Harmful content request patterns ---
_HARMFUL_CONTENT_RULES: list[tuple[str, float]] = [
    # --- Hate / discrimination requests (English) ---
    (r"\b(?:tell|give|write|make|create|generate|share)\b.{0,20}\b(?:racist|sexist|discriminatory|hate|hateful|bigoted|prejudiced|offensive)\b", 0.95),
    (r"\b(?:joke|story|comment|remark|段子|笑话).{0,20}\b(?:racist|discriminatory|hate|hateful|bigoted|prejudiced)\b", 0.90),
    (r"\b(?:mock|insult|demean|belittle|ridicule|derogatory|disparage|贬损|嘲笑|侮辱|贬低).{0,20}\b(?:muslim|jewish|christian|islam|jew|religion|信仰|宗教|穆斯林|犹太|基督)\b", 0.95),
    (r"\b(?:racial|ethnic|race|种族|民族).{0,15}\b(?:discrimination|slur|stereotype|hate|歧视|侮辱|偏见)\b", 0.90),

    # --- Hate / discrimination requests (Chinese) ---
    (r"(?:讲|写|给我|生成|创作|分享|来).{0,20}(?:种族歧视|性别歧视|歧视色彩|歧视性|侮辱性|贬损性|仇恨性)", 0.95),
    (r"(?:笑话|段子|故事|言论|评论|梗).{0,20}(?:种族歧视|性别歧视|歧视色彩|歧视性|侮辱性|贬损性|仇恨性)", 0.90),
    (r"(?:嘲笑|贬损|侮辱|贬低|歧视|嘲讽|蔑视|辱骂).{0,20}(?:穆斯林|犹太|基督|佛教|宗教|信仰|少数民族|特定族群|特定群体)", 0.95),
    (r"(?:专门|特意|特别).{0,15}(?:嘲笑|贬损|侮辱|攻击|歧视|抹黑).{0,20}(?:穆斯林|犹太|基督|宗教|信仰|少数民族|族群|群体)", 0.95),
    (r"(?:贬损性|侮辱性|歧视性|攻击性).{0,10}(?:段子|笑话|言论|故事|内容)", 0.90),
]

_INJECTION_REGEXES = [(re.compile(p, re.IGNORECASE), score) for p, score in _INJECTION_RULES]
_HARMFUL_REGEXES = [(re.compile(p, re.IGNORECASE), score) for p, score in _HARMFUL_CONTENT_RULES]

# Qwen3Guard output category → our RiskCategory mapping
_GUARD_CATEGORY_MAP: dict[str, RiskCategory] = {
    # English category names from model output
    "violent": RiskCategory.harmful_content,
    "violence": RiskCategory.harmful_content,
    "hate": RiskCategory.harmful_content,
    "hate_speech": RiskCategory.harmful_content,
    "sexual_content": RiskCategory.harmful_content,
    "sexual": RiskCategory.harmful_content,
    "self_harm": RiskCategory.harmful_content,
    "harassment": RiskCategory.harmful_content,
    "unethical": RiskCategory.harmful_content,
    "unethical acts": RiskCategory.harmful_content,
    "illegal_activity": RiskCategory.compliance,
    "illegal": RiskCategory.compliance,
    "deception": RiskCategory.compliance,
    "privacy": RiskCategory.pii,
    # Chinese category names that might appear
    "暴力": RiskCategory.harmful_content,
    "仇恨": RiskCategory.harmful_content,
    "色情": RiskCategory.harmful_content,
    "自残": RiskCategory.harmful_content,
    "骚扰": RiskCategory.harmful_content,
    "违法": RiskCategory.compliance,
    "欺诈": RiskCategory.compliance,
    "隐私": RiskCategory.pii,
    "不道德": RiskCategory.harmful_content,
}


class ContentGuardScanner:
    """Content guard scanner: rule-based injection + harmful content + Qwen3Guard model.

    Regex rules provide deterministic detection for known patterns (injection,
    harmful content requests). The Qwen3Guard-Gen-0.6B generative model scans
    for harmful content the rules don't cover, producing structured safe/unsafe
    responses that work well on both Chinese and English text.
    """

    def __init__(self) -> None:
        import app.safety.torch_compat  # noqa: F401
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_name = os.environ.get(
            "GUARD_MODEL", "Qwen/Qwen3Guard-Gen-0.6B"
        )
        logger.info("Loading guard model: %s", model_name)

        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForCausalLM.from_pretrained(model_name)
        self._model.eval()

        logger.info(
            "ContentGuardScanner initialized: injection rules + harmful rules + %s",
            model_name,
        )

    async def scan(self, content: str, source: str) -> ScannerResult:
        """Scan content for injection, harmful content, and guard model violations."""
        try:
            guard_findings = await asyncio.to_thread(self._scan_guard_model, content)
            injection_findings = self._check_injection_rules(content)
            harmful_findings = self._check_harmful_content_rules(content)

            findings = guard_findings + injection_findings + harmful_findings
            logger.info(
                "ContentGuard scan result: source=%s, content=%r, findings_count=%d, "
                "guard=%d, injection=%d, harmful=%d, categories=%s",
                source, content[:100], len(findings),
                len(guard_findings), len(injection_findings), len(harmful_findings),
                [f.category.value for f in findings],
            )
            return ScannerResult(
                findings=findings,
                has_violations=len(findings) > 0,
                scanner_name="content_guard",
            )
        except Exception as e:
            logger.warning("ContentGuardScanner error: %s", e)
            return ScannerResult(findings=[], has_violations=False, scanner_name="content_guard")

    def _scan_guard_model(self, content: str) -> list[ScannerFinding]:
        """Run Qwen3Guard generative model synchronously (called via asyncio.to_thread).

        The model generates structured text: safe/unsafe + category + reason.
        We parse the output to extract the safety decision and risk category.
        """
        findings: list[ScannerFinding] = []
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a content safety guard. Classify whether the content is safe or unsafe. If unsafe, specify the risk category from: violence, hate, sexual_content, self_harm, harassment, illegal_activity, deception, privacy.",
                },
                {
                    "role": "user",
                    "content": f"请判断以下内容是否安全：\n\n{content}",
                },
            ]
            text = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self._tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512
            )
            outputs = self._model.generate(
                **inputs, max_new_tokens=128, temperature=0
            )
            response = self._tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            )
            # Parse response: "Safety: Unsafe" means harmful content
            response_lower = response.lower().strip()
            is_unsafe = (
                "unsafe" in response_lower
                or "不安全" in response_lower
                or "controversial" in response_lower  # borderline — treat as unsafe for enterprise
            )
            category = "none"
            if is_unsafe:
                category = self._extract_category(response_lower)
                risk_cat = _GUARD_CATEGORY_MAP.get(category, RiskCategory.harmful_content)
                findings.append(ScannerFinding(
                    category=risk_cat,
                    confidence=0.9,
                    anonymized_detail=f"Guard model flagged as unsafe ({category})",
                ))

            logger.info(
                "Guard model scan: content=%r, response=%s, decision=%s, category=%s",
                content[:100], response,
                "UNSAFE" if is_unsafe else "SAFE",
                category,
            )
        except Exception as e:
            logger.warning("Guard model scan failed: %s", e)
        return findings

    def _extract_category(self, response: str) -> str:
        """Extract risk category from guard model response text.

        Searches for known category keywords in the response.
        Returns the first matching category, or 'harmful_content' as fallback.
        """
        known_categories = list(_GUARD_CATEGORY_MAP.keys())
        for cat in known_categories:
            if cat in response:
                return cat
        # Chinese category names that might appear
        zh_to_en = {
            "暴力": "violence",
            "仇恨": "hate",
            "色情": "sexual_content",
            "自残": "self_harm",
            "骚扰": "harassment",
            "违法": "illegal_activity",
            "欺诈": "deception",
            "隐私": "privacy",
        }
        for zh, en in zh_to_en.items():
            if zh in response:
                return en
        return "violence"  # default if unsafe but category unclear

    def _check_injection_rules(self, content: str) -> list[ScannerFinding]:
        """Check content against known injection regex patterns."""
        findings: list[ScannerFinding] = []
        for regex, confidence in _INJECTION_REGEXES:
            if regex.search(content):
                findings.append(ScannerFinding(
                    category=RiskCategory.prompt_injection,
                    confidence=confidence,
                    anonymized_detail="Matched injection pattern rule",
                ))
                if confidence >= 0.9:
                    findings.append(ScannerFinding(
                        category=RiskCategory.jailbreak,
                        confidence=confidence,
                        anonymized_detail="Detected jailbreak pattern",
                    ))
        return findings

    def _check_harmful_content_rules(self, content: str) -> list[ScannerFinding]:
        """Check content against harmful content request regex patterns."""
        findings: list[ScannerFinding] = []
        for regex, confidence in _HARMFUL_REGEXES:
            if regex.search(content):
                findings.append(ScannerFinding(
                    category=RiskCategory.harmful_content,
                    confidence=confidence,
                    anonymized_detail="Matched harmful content request pattern",
                ))
        return findings


# Backward-compatible alias so existing imports still work
LLMGuardrailScanner = ContentGuardScanner