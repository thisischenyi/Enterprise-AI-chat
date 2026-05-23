---
phase: 02-safety-pipeline-chat
verified: 2026-05-22T12:00:00Z
status: gaps_found
score: 4/5
overrides_applied: 0
gaps:
  - truth: "Unsafe input is blocked before any model call (in production)"
    status: partial
    reason: "get_safety_pipeline() in chat.py returns SafetyPipeline(scanners=[]) — no scanners wired in production. All content passes as 'allow'. Tests prove logic works with mock scanners, but production deployment would not block anything."
    artifacts:
      - path: "backend/app/api/chat.py"
        issue: "Line 60: scanners=[] means no real scanning in production"
    missing:
      - "Wire DataProtectionScanner and/or LLMGuardrailScanner into get_safety_pipeline() with graceful fallback if deps unavailable"
---

# Phase 2: Safety Pipeline & Chat Verification Report

**Phase Goal:** The safety pipeline reliably blocks unsafe content and employees can chat through it
**Verified:** 2026-05-22T12:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Unsafe input is blocked before any model call, with a block message that explains the risk category without echoing sensitive content | PARTIAL | Pipeline logic verified in tests (test_input_block_path passes, block message never echoes content). But production get_safety_pipeline() has scanners=[] so nothing is actually blocked in production. |
| 2 | Unsafe model output is blocked before display, with a block message that explains the risk category without echoing sensitive content | PARTIAL | Same as above — test_output_block_path passes with mock scanners. Production would not block. |
| 3 | Scanner failures (crash, timeout, error) block content rather than allowing it unfiltered | VERIFIED | SafetyPipeline._scan() returns fail_closed when all scanners fail or timeout. test_fail_closed_path and test_timeout_fail_closed prove this. |
| 4 | Employee can select a model provider and send a chat message that receives a response through the backend | VERIFIED | POST /api/chat/send endpoint fully implemented with input scan -> model call -> output scan flow. GET /api/chat/models returns available models. Frontend ChatPage wired via TanStack Query. test_chat_send_allowed passes. |
| 5 | Automated tests prove the main allow, input block, output block, and fail-closed paths work correctly | VERIFIED | 25 tests pass. test_safety_pipeline.py covers all 4 paths. test_chat_api.py covers endpoint integration. test_fixtures.py provides comprehensive fixtures. |

**Score:** 4/5 truths verified (truths 1+2 share same root cause, counted as one gap)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| backend/app/safety/scanner_interface.py | Scanner protocol + types | VERIFIED | 74 lines, Scanner Protocol, ScannerResult, ScannerFinding, PolicyDecision, RiskCategory |
| backend/app/safety/data_protection.py | Presidio-backed PII scanner | VERIFIED | 117 lines, real AnalyzerEngine with custom recognizers |
| backend/app/safety/llm_guardrails.py | LLM Guard-backed scanner | VERIFIED | 101 lines, PromptInjection + Toxicity scanners |
| backend/app/safety/pipeline.py | SafetyPipeline with fail-closed | VERIFIED | 91 lines, asyncio.wait_for timeout, parallel scanner execution |
| backend/app/safety/policy.py | SafetyPolicy evaluator | VERIFIED | 73 lines, aggregates findings, generates block messages |
| backend/app/safety/block_messages.py | Category-specific templates | VERIFIED | 109 lines, all 6 categories x 2 sources, never echoes content |
| backend/app/safety/custom_recognizers.py | Enterprise PII recognizers | VERIFIED | Exists with EmployeeId, ProjectCode, ChineseNationalId |
| backend/app/audit/repository.py | AuditRepository metadata-only | VERIFIED | 62 lines, records event_id, timestamp, user_id, model_id, categories, action — no raw content |
| backend/app/audit/events.py | AuditEvent model | VERIFIED | SQLAlchemy model exists |
| backend/app/api/chat.py | POST /send + GET /models | VERIFIED | 158 lines, full pipeline flow, auth required |
| backend/app/models/providers.py | ModelProvider ABC + registry | VERIFIED | File exists |
| backend/app/models/qwen.py | QwenProvider | VERIFIED | File exists |
| backend/app/models/openai_compatible.py | OpenAICompatibleProvider | VERIFIED | File exists |
| frontend/src/features/chat/ChatPage.tsx | Chat page with full flow | VERIFIED | 84 lines, handles allowed/blocked/fail_closed |
| frontend/src/stores/chatStore.ts | Zustand chat state | VERIFIED | 37 lines, selectedModel, messages, isLoading |
| frontend/src/features/chat/BlockedMessage.tsx | Blocked message display | VERIFIED | 37 lines |
| backend/app/tests/test_safety_pipeline.py | Pipeline integration tests | VERIFIED | 6 tests covering all paths |
| backend/app/tests/test_chat_api.py | Chat API tests | VERIFIED | 5 tests covering auth + all response statuses |
| backend/app/tests/test_fixtures.py | Safety fixtures | VERIFIED | Mock scanners + fixture definitions |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| chat.py | pipeline.py | pipeline.scan_input() / scan_output() | WIRED | Lines 85, 122 |
| chat.py | providers.py | provider.chat_completion() | WIRED | Line 106 |
| chat.py | audit/repository.py | audit_repo.record_event() | WIRED | Lines 88, 97, 115, 125, 131, 141 |
| pipeline.py | scanner_interface.py | scanner.scan() | WIRED | Line 78 |
| pipeline.py | policy.py | policy.evaluate() | WIRED | Line 74 |
| ChatPage.tsx | lib/api.ts | sendChatMessage() | WIRED | Line 15 |
| chat.py | get_safety_pipeline() | scanners=[] | PARTIAL | No real scanners injected in production |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| backend/app/api/chat.py | 60 | `scanners=[]` empty scanner list in production | WARNING | Pipeline passes all content in production |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| SAFE-01 | 02-01 | Input safety filtering runs before every model call | PARTIAL | Architecture correct, tests pass, but production scanners=[] |
| SAFE-02 | 02-01 | Output safety filtering runs before every response display | PARTIAL | Same as SAFE-01 |
| SAFE-03 | 02-02 | Policy violations block full content — no partial redaction | SATISFIED | SafetyPolicy always returns full block, ChatResponse has unified shape |
| SAFE-04 | 02-01 | Block messages explain risk category without echoing content | SATISFIED | block_messages.py templates never include detected text |
| SAFE-05 | 02-02 | Audit metadata recorded for every decision | SATISFIED | audit_repo.record_event() called on all paths in chat.py |
| SAFE-06 | 02-02 | Audit events contain metadata only | SATISFIED | AuditRepository stores categories, action, anonymized findings only |
| SAFE-07 | 02-02 | Scanner failures default to BLOCK | SATISFIED | Pipeline returns fail_closed on crash/timeout, tests prove it |
| SAFE-08 | 02-01 | Custom Presidio recognizers for enterprise PII | SATISFIED | EmployeeIdRecognizer, ProjectCodeRecognizer, ChineseNationalIdRecognizer |
| CHAT-01 | 02-03 | Employee can select model provider | SATISFIED | GET /api/chat/models + ModelSelector component |
| CHAT-02 | 02-03 | Employee can send message and receive response | SATISFIED | POST /api/chat/send + ChatPage full flow |
| TEST-01 | 02-04 | Tests prove allow path | SATISFIED | test_allow_path, test_chat_send_allowed |
| TEST-02 | 02-04 | Tests prove input block path | SATISFIED | test_input_block_path, test_chat_send_input_blocked |
| TEST-03 | 02-04 | Tests prove output block path | SATISFIED | test_output_block_path |
| TEST-04 | 02-04 | Tests prove fail-closed | SATISFIED | test_fail_closed_path, test_timeout_fail_closed, test_chat_send_fail_closed |
| TEST-05 | 02-04 | Fixtures cover all risk categories | SATISFIED | SAFETY_FIXTURES covers PII, sensitive data, prompt injection, jailbreak, harmful content |

### Human Verification Required

None — all checks are programmatically verifiable.

### Gaps Summary

**One gap with shared root cause:** The production `get_safety_pipeline()` dependency in `backend/app/api/chat.py` line 60 returns `SafetyPipeline(scanners=[], ...)`. This means in a running production server, no content would be blocked because there are no scanners to detect violations.

The scanner implementations (DataProtectionScanner, LLMGuardrailScanner) exist and are substantive, but they are only used in tests via mock wrappers. The real implementations require `presidio-analyzer` and `llm-guard` dependencies which have installation issues (per git log: "llm-guard deps blocked").

**Fix needed:** Wire real scanners into `get_safety_pipeline()` with try/except fallback, or at minimum provide a configuration mechanism to enable them when deps are available.

---

_Verified: 2026-05-22T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
