# Phase 1: Foundation & Auth - Context

**Gathered:** 2026-05-21
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the project skeleton and authentication foundation:
- Backend FastAPI project with full directory structure (per SPEC.md)
- Frontend React + TypeScript + Vite project scaffold
- PostgreSQL database with auth-related tables (users, sessions)
- Mock OIDC authentication that simulates the real OIDC flow
- Authenticated user identity available in all backend routes
- Role distinction: employee (chat access) vs admin (config + audit access)
- Frontend state management (Zustand) and API client (TanStack Query) setup

This phase does NOT deliver: chat functionality, safety pipeline, model integration, conversation history, admin dashboard, streaming.

</domain>

<decisions>
## Implementation Decisions

### Mock Auth UX
- **D-01:** Simulated OIDC flow — click login → fake redirect page → callback → session established. Validates the OIDC adapter pattern for real IDP swap later.
- **D-02:** Role selector on mock page — user picks employee or admin before login, then auto-logged in as that test user. Tests both roles during demo.

### Session Strategy
- **D-03:** Server-side sessions stored in PostgreSQL. Server validates each request by DB lookup. Easy to invalidate, audit-friendly, consistent with project's PostgreSQL-only requirement (no Redis for MVP).

### Frontend Setup
- **D-04:** Zustand for auth/global state management, TanStack Query for API calls. Standard 2025 React pattern, well-suited for chat app with caching needs.

### Backend Structure
- **D-05:** Create full SPEC.md backend directory structure upfront (api/, auth/, models/, safety/, audit/, db/) with placeholder modules. Future phases fill in implementations.

### Claude's Discretion
- Database migration tool choice (Alembic recommended by research — planner decides)
- Frontend component library / CSS approach (planner decides)
- Exact mock OIDC implementation details (adapter pattern, token format)
- DB schema column types and constraints (planner decides)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Definition
- `.planning/PROJECT.md` — Core value, constraints, key decisions, context
- `.planning/REQUIREMENTS.md` — v1 requirements with AUTH-01, AUTH-02, AUTH-03 for this phase
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, requirement mappings
- `SPEC.md` — Full project spec including tech stack, project structure, core flow, boundaries, success criteria

### Research
- `.planning/research/STACK.md` — Specific library recommendations with rationale (itsdangerous for mock OIDC, Authlib for real OIDC, SQLAlchemy 2, asyncpg, etc.)
- `.planning/research/SUMMARY.md` — Research synthesis with roadmap implications

### Key Decisions
- `.planning/notes/key-decisions.md` — Four key decisions including mock OIDC strategy and Presidio/LLM Guard choices
- `.planning/seeds/oidc-provider-integration.md` — Seed for real OIDC swap when enterprise IDP confirmed

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
None — greenfield project, no existing code.

### Established Patterns
None — patterns will be established in this phase and carried forward.

### Integration Points
- Backend auth middleware → all future API endpoints will depend on authenticated user identity
- Frontend auth state (Zustand) → all future features will check auth state before rendering
- Database schema → Phase 2-4 tables will be added to the same PostgreSQL instance

</code_context>

<specifics>
## Specific Ideas

- Mock OIDC should simulate real OIDC flow (redirect → callback) to validate the adapter pattern works before real IDP swap
- Role selector on mock login page lets testers switch between employee and admin roles quickly
- Server-side sessions in PostgreSQL (no Redis dependency for MVP)
- Full backend directory structure upfront per SPEC.md — placeholder modules for safety, models, audit directories

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 1-Foundation & Auth*
*Context gathered: 2026-05-21*