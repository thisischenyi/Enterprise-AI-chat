---
phase: "02"
plan: "04"
subsystem: safety-pipeline-tests
tags: [testing, safety, integration, pipeline]
dependency_graph:
  requires: [02-01, 02-02, 02-03]
  provides: [safety-pipeline-test-coverage, chat-api-test-coverage]
  affects: [backend/app/tests/]
tech_stack:
  added: []
  patterns: [mock-scanner-pattern, dependency-override-testing]
key_files:
  created:
    - backend/app/tests/test_fixtures.py
    - backend/app/tests/test_safety_pipeline.py
    - backend/app/tests/test_chat_api.py
  modified:
    - backend/app/tests/test_role_access.py
decisions:
  - "Used mock scanners instead of real ML models for test speed (real scanners need spaCy + LLM Guard model downloads)"
  - "Scoped dependency overrides to test module via autouse fixture to avoid polluting other test files"
metrics:
  duration: "8 minutes"
  completed: "2026-05-22"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 02 Plan 04: Safety Pipeline Tests Summary

Automated tests proving the safety pipeline works on all four core paths with 18 synthetic fixtures covering every risk category.

## One-liner

Mock-based integration tests proving allow/block/fail-closed pipeline paths plus chat API endpoint coverage with 25 total tests passing.

## Completed Tasks

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Test fixtures + fixture validation | a9019a3 | backend/app/tests/test_fixtures.py |
| 2 | Pipeline integration + chat API tests | 868fe70 | backend/app/tests/test_safety_pipeline.py, test_chat_api.py |

## Test Coverage

- **test_fixtures.py** (5 tests): Validates mock scanners detect PII, sensitive data, Chinese national ID, prompt injection, jailbreak, harmful content; safe content passes clean
- **test_safety_pipeline.py** (6 tests): allow path, input block, output block, fail-closed (crash), fail-closed (timeout), aggregated multi-category findings
- **test_chat_api.py** (5 tests): POST /send allowed, POST /send blocked, POST /send fail_closed, GET /models, 401 unauthenticated

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed pre-existing test_role_access.py assertions**
- **Found during:** Task 2
- **Issue:** test_employee_access_chat_endpoint and test_admin_access_chat_endpoint expected old `{"message": ..., "user_role": ...}` response format, but chat/models API was refactored in plan 02-03 to return a list of ModelInfo objects
- **Fix:** Updated assertions to `assert isinstance(data, list)` matching the new API contract
- **Files modified:** backend/app/tests/test_role_access.py
- **Commit:** 868fe70

## Verification

```
25 passed, 39 warnings in 0.61s
```

All existing auth tests + new safety tests pass together.

## Self-Check: PASSED
