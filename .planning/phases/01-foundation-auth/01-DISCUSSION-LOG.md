# Phase 1: Foundation & Auth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-21
**Phase:** 1-Foundation & Auth
**Areas discussed:** Mock Auth UX, Session Strategy, Frontend Setup, Backend Structure

---

## Mock Auth UX

| Option | Description | Selected |
|--------|-------------|----------|
| Simulated OIDC flow | Simulates real OIDC: click login → fake redirect → callback → session. Validates adapter pattern for real IDP swap. | ✓ |
| Simple login form | Email/password form that always succeeds. Easier but doesn't validate OIDC adapter pattern. | |
| Auto-login | Automatically signed in as test user on page load. Fastest but doesn't test auth UI. | |

**User's choice:** Simulated OIDC flow (Recommended)

| Option | Description | Selected |
|--------|-------------|----------|
| Role selector on mock page | User picks role (employee/admin) before login. Good for testing both roles. | ✓ |
| Default employee, admin via config | Fixed test user (employee). Admin requires env/DB change. | |
| Pre-seeded test accounts | Multiple test accounts in DB, user selects which. | |

**User's choice:** Role selector on mock page

**Notes:** Simulated OIDC flow is critical because it validates the adapter pattern — the mock must mimic real OIDC (redirect, callback, token exchange) so swapping in real IDP later only requires an adapter change, not route-level surgery.

---

## Session Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Server-side sessions in DB | Sessions in PostgreSQL. Server validates via DB lookup. Easy to invalidate, audit-friendly. | ✓ |
| JWT in httpOnly cookie | Signed JWT, no DB lookup per request, faster. Harder to invalidate mid-session. | |
| Redis sessions | Fast but adds infrastructure dependency for MVP. | |

**User's choice:** Server-side sessions in DB (Recommended)

**Notes:** Consistent with PostgreSQL-only requirement. No Redis dependency needed for MVP. Audit-friendly since session records are in DB.

---

## Frontend Setup

| Option | Description | Selected |
|--------|-------------|----------|
| Zustand + TanStack Query | Zustand for auth/global state, TanStack Query for API calls. Standard 2025 pattern. | ✓ |
| Context + fetch (minimal) | React Context for auth, fetch/axios for API. Simpler but less scalable for chat app. | |
| You decide | Let planner decide based on CONTEXT.md constraints. | |

**User's choice:** Zustand + TanStack Query (Recommended)

**Notes:** TanStack Query provides caching, retry, and optimistic update patterns that are well-suited for a chat app with real-time updates.

---

## Backend Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Full SPEC structure upfront | Create all directories per SPEC.md (api/, auth/, models/, safety/, audit/, db/) with placeholder modules. Future phases fill in. | ✓ |
| Minimal — only Phase 1 dirs | Only create directories needed for Phase 1. Add others when their phases start. | |

**User's choice:** Full SPEC structure upfront (Recommended)

**Notes:** Having placeholder modules in all directories sets clear integration points for future phases and prevents structural drift.

---

## Claude's Discretion

- Database migration tool choice (Alembic recommended)
- Frontend component library / CSS approach
- Exact mock OIDC implementation details (adapter pattern, token format)
- DB schema column types and constraints

## Deferred Ideas

None — all discussion stayed within Phase 1 scope.