# Walking Skeleton — Enterprise AI Chat MVP

**Phase:** 1
**Generated:** 2026-05-21

## Capability Proven End-to-End

A user can pick a role (employee or admin), sign in through mock OIDC authentication, and see their identity and role displayed on a page, with the backend enforcing role-based access to admin-only vs chat endpoints.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework (backend) | FastAPI 0.115+ with async | Native async support for streaming; Pydantic v2 integration; dependency injection for auth middleware; OpenAPI docs auto-generated |
| Framework (frontend) | React 19 + TypeScript 5.7 + Vite 6 | Standard 2025 React SPA stack; Vite provides fast HMR and ESM builds; TypeScript for enterprise code quality |
| Data layer | PostgreSQL 16 + SQLAlchemy 2 async + asyncpg + Alembic | SQLAlchemy 2 native async support for FastAPI; asyncpg for non-blocking DB access; Alembic for schema migrations as future phases add tables |
| Auth | Mock OIDC (itsdangerous TimedSerializer) + server-side PostgreSQL sessions + FastAPI Depends | itsdangerous signs session tokens; sessions stored in DB and validated by lookup on each request; adapter pattern in MockOIDCProvider allows real IDP swap without changing downstream code |
| Deployment target | Local development (uvicorn --reload + npm run dev + local PostgreSQL) | MVP runs locally first; deployment strategy deferred per key decision D-04 |
| Directory layout (backend) | backend/app/ with api/, auth/, models/, safety/, audit/, db/ per SPEC.md | Feature-area modules align with pipeline architecture; placeholder modules established for future phases |
| Directory layout (frontend) | frontend/src/ with features/auth/, features/admin/, stores/, lib/, app/ | Feature-folder pattern for vertical slices; stores/ for Zustand state; lib/ for shared API client |

## Stack Touched in Phase 1

- [x] Project scaffold (FastAPI backend + React/Vite/TS frontend; ruff + Vitest configured)
- [x] Routing — frontend routes (/login, /mock-oidc, /auth/callback, /, /admin) + backend API routes (/api/auth/*, /api/admin/*, /api/chat/*)
- [x] Database — PostgreSQL with users and sessions tables; Alembic initial migration applied; seed data with 2 test users
- [x] UI — mock OIDC login page with role selector; authenticated home page showing user identity; admin stub page
- [x] Auth pipeline — full mock OIDC flow: login initiation, fake redirect page, callback, session creation, session validation, role-based access enforcement

## Out of Scope (Deferred to Later Slices)

- Chat functionality (Phase 2: Safety Pipeline & Chat)
- Safety pipeline / content filtering (Phase 2)
- Model provider integration (Phase 2)
- Conversation history (Phase 3)
- Streaming responses with safety buffer (Phase 4)
- Admin dashboard with real configuration UI (Phase 4)
- Real OIDC integration (when enterprise IDP confirmed)
- Password reset, email verification, multi-tenancy
- Redis session cache
- Docker/Kubernetes deployment

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: Safety Pipeline & Chat — input/output filtering pipeline + model gateway + non-streaming chat endpoint (adds safety/ and models/ implementations, replaces api/chat.py stub)
- Phase 3: Conversation History & Chat Interface — conversation list, resume, allowed-through content storage (adds conversation UI, Message model)
- Phase 4: Streaming & Admin Dashboard — SSE streaming with safety buffer + admin configuration UI (adds streaming infrastructure, replaces api/admin.py stub)