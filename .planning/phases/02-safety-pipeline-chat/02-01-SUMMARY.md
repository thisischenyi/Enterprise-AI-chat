---
phase: "02"
plan: "01"
subsystem: safety-scanners
tags: [presidio, llm-guard, pii-detection, prompt-injection, safety-pipeline]
dependency_graph:
  requires: []
  provides: [Scanner, ScannerResult, ScannerFinding, PolicyDecision, RiskCategory, DataProtectionScanner, LLMGuardrailScanner, get_block_message]
  affects: [02-02-pipeline, 02-03-chat-api]
tech_stack:
  added: [presidio-analyzer, presidio-anonymizer, spacy, llm-guard, torch]
  patterns: [asyncio.to_thread-for-sync-libs, protocol-based-scanner-interface]
key_files:
  created:
    - backend/app/safety/scanner_interface.py
    - backend/app/safety/block_messages.py
    - backend/app/safety/data_protection.py
    - backend/app/safety/llm_guardrails.py
    - backend/app/safety/torch_compat.py
  modified:
    - backend/app/safety/custom_recognizers.py
    - backend/requirements.txt
    - backend/.env.example
decisions:
  - "llm-guard 0.3.x uses PromptInjection and Toxicity class names (not *Scanner suffix)"
  - "No separate Jailbreak scanner in llm-guard — PromptInjection covers both, dual-mapped at high risk"
  - "torch.jit.script patched to no-op before llm-guard import for compatibility"
  - "ChineseNationalIdRecognizer uses fixed score (0.85) instead of nonexistent _calculate_score method"
metrics:
  duration: "15min"
  completed: "2026-05-22"
  tasks_completed: 3
  tasks_total: 3
---

# Phase 02 Plan 01: Scanner Interface and Implementations Summary

Presidio-backed PII scanner and LLM Guard-backed guardrail scanner with async wrappers, custom enterprise recognizers, and category-specific block messages.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 59ba2fa | Scanner interface types + block message templates |
| 2 | ddb3d24 | DataProtectionScanner with Presidio + custom recognizers |
| 3 | 5cec540 | LLMGuardrailScanner with PromptInjection + Toxicity |

## What Was Built

1. **Scanner Protocol + Types** (Task 1): RiskCategory enum, ScannerFinding, ScannerResult, PolicyDecision dataclasses, Scanner Protocol with async scan method.

2. **Block Messages** (Task 1): 12 templates (6 categories x 2 sources) with revision hints, severity-ordered selection, fail-closed fallback. Never echo detected content.

3. **DataProtectionScanner** (Task 2): Wraps Presidio AnalyzerEngine with spaCy en_core_web_lg. Registers 3 custom recognizers (EmployeeId, ProjectCode, ChineseNationalId with checksum). Maps entity types to RiskCategory. Async via asyncio.to_thread().

4. **LLMGuardrailScanner** (Task 3): Wraps llm-guard PromptInjection + Toxicity scanners. torch.jit.script patched to no-op for compatibility. PromptInjection findings dual-mapped to jailbreak at risk >= 0.9. Individual scanner failures caught.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed custom_recognizers.py invalid import**
- **Found during:** Task 2
- **Issue:** `from presidio_analyzer.context import ContextWordExtractor` does not exist in presidio-analyzer 2.2.x
- **Fix:** Removed unused import
- **Files modified:** backend/app/safety/custom_recognizers.py

**2. [Rule 1 - Bug] Fixed Pattern() constructor parameter name**
- **Found during:** Task 2
- **Issue:** Presidio Pattern uses `score` parameter, not `strength`
- **Fix:** Renamed all `strength=` to `score=` in custom recognizers
- **Files modified:** backend/app/safety/custom_recognizers.py

**3. [Rule 1 - Bug] Fixed ChineseNationalIdRecognizer._calculate_score**
- **Found during:** Task 2
- **Issue:** `_calculate_score` method does not exist on PatternRecognizer
- **Fix:** Use fixed score of 0.85 for checksum-valid IDs
- **Files modified:** backend/app/safety/custom_recognizers.py

**4. [Rule 3 - Blocking] Created torch_compat.py for llm-guard compatibility**
- **Found during:** Task 3
- **Issue:** torch.jit.script causes issues when llm-guard imports models
- **Fix:** Created patch module imported before llm-guard
- **Files modified:** backend/app/safety/torch_compat.py

## Self-Check: PASSED
