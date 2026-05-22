---
phase: 02-safety-pipeline-chat
plan: 05
status: complete
started: 2026-05-22T16:25:00Z
completed: 2026-05-22T16:28:00Z
duration_minutes: 3
gap_closure: true
---

# Plan 02-05 Summary: Wire Real Scanners into Production Pipeline

## One-Liner
Wired DataProtectionScanner and LLMGuardrailScanner into get_safety_pipeline() with graceful per-scanner fallback.

## What Was Built
- `get_safety_pipeline()` now instantiates both real scanners with try/except per scanner
- torch_compat imported before LLMGuardrailScanner to apply torch.jit monkey-patch
- Fixed custom_recognizers.py missing `supported_entity` positional argument for PatternRecognizer

## Key Files
- `backend/app/api/chat.py` — get_safety_pipeline() wires real scanners
- `backend/app/safety/custom_recognizers.py` — added supported_entity to all 3 recognizers

## Deviations
- Fixed pre-existing bug in custom_recognizers.py (missing `supported_entity` argument caused DataProtectionScanner init to fail)

## Verification
- 25 tests pass
- Production pipeline initializes with 2 scanners (DataProtectionScanner + LLMGuardrailScanner)

## Self-Check: PASSED
