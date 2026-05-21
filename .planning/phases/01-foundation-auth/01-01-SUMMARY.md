---
phase: 01-foundation-auth
plan: 01
subsystem: auth
tags: [backend, auth, mock-oidc, sqlalchemy, tdd]
dependency_graph:
  requires: []
  provides: [mock-oidc-auth, session-management, auth-middleware]
  affects: [all-future-api-endpoints]
tech_stack:
  added: [fastapi, sqlalchemy-2-async, asyncpg, itsdangerous, aiosqlite]
  patterns: [adapter-pattern-oidc, dependency-injection-fastapi, session-cookie-auth]
key_files:
  created:
    - backend/app/main.py
    - backend/app/api/auth.py
    - backend/app/api/chat.py
    - backend/app/api/admin.py
    - backend/app/auth/oidc.py
    - backend/app/auth/current_user.py
    - backend/app/db/schema.py
    - backend/app/db/__init__.py
    - backend/app/db/seed_data.py
    - backend/app/db/migrations/env.py
    - backend/app/db/migrations/versions.py
    - backend/app/tests/test_auth.py
    - backend/requirements.txt
    - backend/.env.example
    - backend/alembic.ini
    - backend/alembic/env.py
  modified:
    - backend/app/db/schema.py
    - backend/app/db/__init__.py
    - backend/requirements.txt
decisions:
  - "Use SQLite (aiosqlite) for testing via dependency override; PostgreSQL for production"
  - "Use naive UTC datetimes for DB compatibility across PostgreSQL and SQLite"
  - "OIDCProvider ABC with adapter pattern for future real IDP swap"
metrics:
  duration: 13 minutes
  completed: 2026-05-21
  tasks_completed: 2
  files_created: 29
  files_modified: 3
---

# Phase 1 Plan 01: Backend Walking Skeleton Summary

Mock OIDC authentication with session management in PostgreSQL, auth middleware, and full backend project scaffold per SPEC.md -- all 3 auth tests pass end-to-end.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Backend project scaffold + DB schema + failing auth test (RED) | d8f77d9 | 33 files (full backend directory structure) |
| 2 | Implement mock OIDC auth routes + middleware (GREEN) | a50852a | 7 files modified (auth.py, oidc.py, current_user.py, schema.py, db/__init__.py, test_auth.py, requirements.txt) |

## Key Implementation Details

### Task 1 (RED): Backend Project Scaffold
- Created full backend directory structure per SPEC.md with all placeholder modules
- api/ (auth, chat stub, admin stub), auth/ (oidc, current_user), db/ (schema, migrations, seed_data), models/ (providers, qwen, openai_compatible), safety/ (pipeline, data_protection, llm_guardrails, policy), audit/ (events, repository), tests/
- SQLAlchemy 2 async schema: User and Session models with UUIDs, role CHECK constraint
- Alembic migration config with async engine setup
- Auth middleware stub returning 401 for all requests
- MockOIDCProvider stub with placeholder responses
- 2 failing tests (callback no cookie, /me no user), 1 passing test (/me returns 401)

### Task 2 (GREEN): Mock OIDC Auth Implementation
- MockOIDCProvider: full implementation with OIDCProvider ABC adapter pattern, itsdangerous TimedSerializer for token signing
- Login route: generates signed state_token, validates role parameter
- Callback route: validates state_token signature, creates/finds user in DB, creates session row, sets HttpOnly session cookie
- Me route: Depends(get_current_user) returns authenticated user identity {id, email, name, role}
- get_current_user: session cookie extraction, DB lookup, expiry check (fail-closed per T-01-02)
- get_admin_user: role check raises 403 for non-admin (per T-01-04, AUTH-03 partial)
- Tests use SQLite via dependency override (PostgreSQL not installed on dev machine)
- All 3 tests pass: authenticated access returns user, unauthenticated returns 401, callback creates session

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] PostgreSQL not installed, tests use SQLite via dependency override**
- **Found during:** Task 2 execution
- **Issue:** PostgreSQL is not installed on the development machine; tests need a database to work
- **Fix:** Added aiosqlite as test dependency, created test DB dependency override using in-memory SQLite, seeded test users via fixture
- **Files modified:** requirements.txt (added aiosqlite), test_auth.py (dependency override pattern), db/__init__.py (commit/rollback in session yield)
- **Commit:** a50852a
- **Impact:** Production still targets PostgreSQL (asyncpg); tests use SQLite via FastAPI dependency_overrides. Same SQLAlchemy models work on both.

**2. [Rule 1 - Bug] Timezone-aware vs timezone-naive datetime comparison**
- **Found during:** Task 2 execution (test_me_with_valid_session test)
- **Issue:** SQLite strips timezone info on read; comparing timezone-aware datetime.now(timezone.utc) with timezone-naive DB value raised TypeError
- **Fix:** Use naive UTC datetimes throughout (datetime.utcnow()); handle both timezone-aware and timezone-naive in current_user comparison
- **Files modified:** auth/current_user.py, api/auth.py
- **Commit:** a50852a

## Auth Gates

None -- no authentication errors encountered.

## Known Stubs

| File | Stub | Reason |
|------|------|--------|
| backend/app/api/chat.py | Stub endpoint returning {"message": "Chat endpoint - Phase 2"} | Phase 2 will implement full chat API |
| backend/app/api/admin.py | Stub endpoint returning {"message": "Admin endpoint - Phase 4"} | Phase 4 will implement admin dashboard API |
| backend/app/models/providers.py | ModelProvider stub class | Phase 2 will implement provider interface |
| backend/app/models/qwen.py | QwenProvider stub class | Phase 2 will implement Qwen API integration |
| backend/app/models/openai_compatible.py | OpenAICompatibleProvider stub class | Phase 2 will implement local LLM calls |
| backend/app/safety/pipeline.py | SafetyPipeline stub class | Phase 2 will implement safety pipeline |
| backend/app/safety/data_protection.py | DataProtectionScanner stub class | Phase 2 will implement Presidio wrapper |
| backend/app/safety/llm_guardrails.py | LLMGuardrailScanner stub class | Phase 2 will implement LLM Guard wrapper |
| backend/app/safety/policy.py | SafetyPolicy stub class | Phase 2 will implement policy engine |
| backend/app/audit/events.py | AuditEvent stub class | Phase 2 will implement audit event schema |
| backend/app/audit/repository.py | AuditRepository stub class | Phase 2 will implement audit persistence |

All stubs are intentional placeholders per D-05 (full directory structure upfront). They do not prevent the plan's goal (auth pipeline) from being achieved. Each stub will be replaced by its implementing phase.

## Threat Flags

No new threat surface beyond what the plan's threat_model covers. All mitigations from T-01-01 through T-01-04 are implemented:
- T-01-01: itsdangerous TimedSerializer validates mock token signature
- T-01-02: session validated via DB lookup, fail-closed for missing/expired sessions
- T-01-03: HttpOnly session cookie set (Secure=False for local dev, configurable for production)
- T-01-04: get_admin_user dependency checks role == "admin", raises 403 for employees

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED | d8f77d9 (test commit) | PASS -- 2 tests fail, 1 passes |
| GREEN | a50852a (feat commit) | PASS -- all 3 tests pass |
| REFACTOR | -- | Not needed -- code is clean as-is |

Both TDD gates present and valid. RED gate had correct failing tests before implementation. GREEN gate made all tests pass without modifying test expectations.

## Verification

```
cd backend && .venv/Scripts/python -m pytest app/tests/test_auth.py -v
=== 3 passed in 1.03s ===
```

FastAPI routes registered: /api/auth/login, /api/auth/callback, /api/auth/me, /health

## Success Criteria Status

- [x] Backend FastAPI app starts and serves authenticated endpoints
- [x] Mock OIDC login/callback/me route handlers registered
- [x] SQLAlchemy schema defines users and sessions tables (with seed data in test fixture)
- [x] Auth middleware returns authenticated User object on valid session, 401 on missing/expired session
- [x] All 3 test_auth tests pass: authenticated access, unauthenticated access, callback flow

## Self-Check: PASSED

- All 7 key files verified as existing on disk
- Both commit hashes (d8f77d9, a50852a) found in git log
- All 3 auth tests pass: 3 passed in 1.19s