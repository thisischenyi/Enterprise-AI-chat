# Phase 2: Safety Pipeline & Chat - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-21
**Phase:** 2-Safety Pipeline & Chat
**Areas discussed:** Block message design, Chat interaction flow, Scanner activation scope, Custom PII recognizers, Scanner failure handling, Audit event schema, Test fixture design

---

## Block Message Design

| Option | Description | Selected |
|--------|-------------|----------|
| Category-specific templates | Each risk category has a fixed template explaining the category without echoing content. Consistent, predictable, no attacker hints. | ✓ |
| Generic block message | Single generic message: "Content blocked due to safety policy." No category revealed — maximum safety, minimal user guidance. | |
| Category + severity detail | Category + severity level revealed. More helpful for legitimate mistakes but reveals more detection detail. | |

**User's choice:** Category-specific templates
**Notes:** Aligns with SAFE-04 — explain risk category without echoing sensitive content.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Different for input vs output | Input: "Your message was blocked...", Output: "The response was blocked..." User can tell which side caught it. | ✓ |
| Same template for both | Same wording regardless of side. Simpler, but user can't distinguish input vs output blocks. | |

**User's choice:** Different for input vs output

---

| Option | Description | Selected |
|--------|-------------|----------|
| Align with SAFE requirements | 5-6 categories mapping to SAFE-01/02: PII, sensitive data, prompt injection, jailbreak, harmful content, compliance. | ✓ |
| Simplified 3-category grouping | Broad: "personal information", "unsafe content", "policy violation". Fewer templates but less specific. | |

**User's choice:** Align with SAFE requirements

---

| Option | Description | Selected |
|--------|-------------|----------|
| Include revision hint | Add suggestion like "Please remove any personal information and try again." Helps legitimate mistakes. | ✓ |
| No revision hint | Just category explanation. Minimal guidance, maximum safety. | |
| You decide | Claude discretion — planner picks. | |

**User's choice:** Include revision hint

---

## Chat Interaction Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Message + model per request | Each request includes message text + selected model ID. Explicit, simple, user consciously picks provider. | ✓ |
| Session-level model selection | User selects model once per session in Zustand. Simpler request but more state. | |
| You decide | Claude discretion. | |

**User's choice:** Message + model per request

---

| Option | Description | Selected |
|--------|-------------|----------|
| Distinct allowed vs blocked shapes | Allowed: {role, content, model, timestamp}, Blocked: {blocked, category, message, hint}. Two shapes to handle. | |
| Unified response with status field | Single shape: {status: 'allowed'|'blocked', ...common_fields, ...conditional}. One type, conditional rendering. | |
| You decide | Claude discretion — planner picks cleanest API design. | ✓ |

**User's choice:** You decide (Claude discretion)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Model list endpoint | GET /api/chat/models returns available providers dynamically. Backend checks credentials. | ✓ |
| Hardcoded provider list | Fixed providers in frontend config. Simpler but can't adapt to admin changes. | |
| You decide | Claude discretion. | |

**User's choice:** Model list endpoint

---

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated /chat page | Full-width chat area with model selector. Room for Phase 3 sidebar. | ✓ |
| Embedded on home page | Chat component on home page after login. Less room for expansion. | |
| You decide | Claude discretion — planner picks. | |

**User's choice:** Dedicated /chat page

---

## Scanner Activation Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Broad enablement | All Presidio recognizers + LLM Guard PromptInjection + Jailbreak + Toxicity. Covers SAFE-01/02. Some false positives acceptable for MVP. | ✓ |
| Focused minimum set | Only enterprise-relevant Presidio recognizers + LLM Guard PromptInjection + Jailbreak. Fewer false positives but may miss edge cases. | |
| You decide | Claude discretion — broad set for MVP, tune later. | |

**User's choice:** Broad enablement

---

| Option | Description | Selected |
|--------|-------------|----------|
| Same scanners for both input and output | Both sides go through DataProtectionScanner + LLMGuardrailScanner. Consistent, catches PII in model responses. | ✓ |
| Different scanners per side | Input: full pipeline, Output: guardrails only (skip PII). Slightly faster output scanning. | |

**User's choice:** Same scanners for both

---

| Option | Description | Selected |
|--------|-------------|----------|
| Block on first violation | Stop scanning after first finding. Faster for blocked content, but audit only records first finding. | |
| Run all, aggregate findings | Run all scanners regardless, aggregate violations. Slower for blocked content, but comprehensive audit for compliance. | ✓ |
| You decide | Claude discretion — run all for MVP. | |

**User's choice:** Run all, aggregate findings

---

## Custom PII Recognizers

| Option | Description | Selected |
|--------|-------------|----------|
| All three recognizers | Employee ID, project code, Chinese national ID. Full SAFE-08 coverage. | ✓ |
| Chinese national ID only | Highest-risk PII type. Employee IDs and project codes deferred. | |
| You decide | Claude discretion — implement all three. | |

**User's choice:** All three recognizers

---

| Option | Description | Selected |
|--------|-------------|----------|
| Regex-based recognizers | Simple pattern matching. Fast to implement, but less context-aware. | |
| NLP-enhanced recognizers | Use spaCy context words for context-aware detection. Better accuracy, leverages existing NLP engine. | ✓ |

**User's choice:** NLP-enhanced recognizers

---

| Option | Description | Selected |
|--------|-------------|----------|
| With checksum validation | Chinese national ID last digit computed from first 17. Validation reduces false positives from random 18-digit strings. | ✓ |
| Pattern match only | Detect 18-digit sequences near context words. Simpler but more false positives. | |

**User's choice:** With checksum validation

---

## Scanner Failure Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Timeout → block | Scanner timeout triggers fail-closed blocking. Prevents hanging requests. | ✓ |
| No timeout, only crash → block | Fail-closed only on explicit crashes. Risk of hanging on slow scanners. | |

**User's choice:** Timeout triggers fail-closed

---

| Option | Description | Selected |
|--------|-------------|----------|
| 10 seconds per scanner | Per-scanner timeout. FastAPI async — 10s generous for local library calls. | |
| 30 seconds for full pipeline | Pipeline-level timeout. More forgiving, ensures complete pipeline within 30s. | ✓ |
| You decide | Claude discretion — 10s per scanner is standard. | |

**User's choice:** 30 seconds for full pipeline

---

| Option | Description | Selected |
|--------|-------------|----------|
| Different messages for block vs failure | Safety block: category + revision hint. Failure: "system error, please retry." Clear distinction. | ✓ |
| Same message for both | Both return same block message. Prevents probing but users can't retry system errors. | |

**User's choice:** Different messages for block vs failure

---

## Audit Event Schema

| Option | Description | Selected |
|--------|-------------|----------|
| Comprehensive metadata | event_id, timestamp, user_id, model_id, source, risk_categories, policy_action, scanner_findings_summary (anonymized). Covers SAFE-05/06. | ✓ |
| Minimum SAFE-05/06 fields | event_id, timestamp, user_id, risk_categories, policy_action only. Simpler but less useful for admin analysis. | |

**User's choice:** Comprehensive metadata

---

| Option | Description | Selected |
|--------|-------------|----------|
| SQLAlchemy JSON type | JSON stored as TEXT in SQLite, JSONB in PostgreSQL. Same code works for both. | ✓ |
| Normalized tables instead | Separate audit_findings table with one row per finding. No JSON needed. More rows but fully structured. | |

**User's choice:** SQLAlchemy JSON type (user noted MVP uses SQLite)

---

## Test Fixture Design

| Option | Description | Selected |
|--------|-------------|----------|
| Synthetic crafted samples | Controlled triggers for each category. Predictable, no real sensitive data risk. | ✓ |
| Realistic format samples | Realistic enterprise-style inputs with realistic formats but no real PII. More realistic testing. | |

**User's choice:** Synthetic crafted samples

---

| Option | Description | Selected |
|--------|-------------|----------|
| All categories + safe fixtures | ~15-20 fixtures covering PII, sensitive data, injection, jailbreak, harmful content, unsafe output, failure, safe content. | ✓ |
| Minimum per test path | ~5-7 fixtures covering one per test path. Extend later. | |
| You decide | Claude discretion — cover all categories. | |

**User's choice:** All categories + safe fixtures

---

| Option | Description | Selected |
|--------|-------------|----------|
| Include Chinese-language fixtures | Chinese text with national ID patterns. Validates custom recognizers with real enterprise text. | ✓ |
| English-only fixtures | English with 18-digit pattern for Chinese national ID. Simpler but doesn't test real Chinese text context. | |

**User's choice:** Include Chinese-language fixtures

---

## Claude's Discretion

- Chat response shape (unified vs distinct) — planner decides
- Exact Presidio recognizer enablement — researcher verifies
- Exact LLM Guard configuration parameters — researcher verifies
- DB audit_events migration details — planner decides
- Scanner timeout implementation mechanism — planner decides

## Deferred Ideas

None — discussion stayed within phase scope