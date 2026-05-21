# Phase 2: Safety Pipeline & Chat - Context

**Gathered:** 2026-05-21
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the core safety engine and chat interaction:
- Safety scanning pipeline (input scan → model call → output scan) with fail-closed semantics
- DataProtectionScanner implementation wrapping Microsoft Presidio for PII detection and data classification
- LLMGuardrailScanner implementation wrapping ProtectAI LLM Guard for jailbreak, prompt injection, harmful content, and compliance checks
- Model provider gateway (Qwen + OpenAI-compatible) behind ModelProvider interface
- Non-streaming chat endpoint (CHAT-01, CHAT-02) with authenticated user identity
- Block message responses with category-specific templates and revision hints
- Audit event recording with comprehensive metadata (SAFE-05, SAFE-06)
- Custom Presidio recognizers for enterprise PII (employee IDs, project codes, Chinese national IDs) (SAFE-08)
- Automated test coverage proving allow, input-block, output-block, and fail-closed paths (TEST-01 through TEST-05)

This phase does NOT deliver: streaming responses (Phase 4), conversation history persistence (Phase 3), admin dashboard (Phase 4), conversation browsing.

</domain>

<decisions>
## Implementation Decisions

### Block Message Design
- **D-BM01:** Category-specific templates for each risk category, aligned with SAFE requirements — PII/sensitive data, prompt injection, jailbreak attempt, harmful content, compliance violation. Each template explains the risk category without echoing detected content.
- **D-BM02:** Different wording for input block ("Your message was blocked because it contains [category]...") vs output block ("The response was blocked because it contains [category]..."). User can tell which side of the pipeline caught the issue.
- **D-BM03:** Include revision hint per category — e.g., "Please remove any personal information and try again" or "Please rephrase without harmful language." Helps legitimate users correct mistakes.

### Chat Interaction Flow
- **D-CF01:** Message + model per request — each chat request explicitly specifies the model provider ID. No session-level model binding. Backend validates model availability and credentials.
- **D-CF02:** Response shape — Claude discretion. Planner decides between unified response with status field (`{status: 'allowed'|'blocked', ...common_fields, ...conditional_fields}`) or distinct allowed/block shapes.
- **D-CF03:** Model list endpoint (GET /api/chat/models) returns available providers with id, name, description. Backend checks which providers have valid credentials configured.
- **D-CF04:** Dedicated /chat page route for the chat interface — full-width chat area with model selector at top. Room for future conversation list sidebar (Phase 3).

### Scanner Activation Scope
- **D-SA01:** Broad enablement — all Presidio built-in recognizers (PERSON, EMAIL, PHONE, CREDIT_CARD, SSN, IBAN, etc.) + LLM Guard PromptInjection, Jailbreak, and Toxicity scanners. Covers all SAFE-01/02 categories. Some false positives acceptable for MVP — tune later.
- **D-SA02:** Same scanner set for both input and output scanning. DataProtectionScanner + LLMGuardrailScanner run on both sides. Consistent detection, catches PII leaking in model responses.
- **D-SA03:** Run all scanners regardless of early findings, aggregate all violations for comprehensive audit record. Blocked content gets all risk categories documented — better for enterprise compliance analysis.

### Custom PII Recognizers
- **D-PI01:** All three enterprise recognizers for MVP: employee ID (EMP-XXXX pattern), project code (PRJ-XXXX or internal format), Chinese national ID (18-digit). Full SAFE-08 coverage.
- **D-PI02:** NLP-enhanced recognizers using spaCy context words for context-aware detection — e.g., "my employee ID is..." triggers better than pure regex. Leverages existing spaCy engine already required for Presidio.
- **D-PI03:** Chinese national ID recognizer includes checksum validation — last digit computed from first 17 digits. Reduces false positives from random 18-digit strings.

### Scanner Failure Handling
- **D-SF01:** Scanner timeout triggers fail-closed blocking. If the pipeline doesn't complete within the timeout, content is blocked rather than allowed unfiltered (SAFE-07).
- **D-SF02:** 30-second timeout for the full pipeline (not per-scanner). Generous enough for Presidio + LLM Guard combined execution, but prevents hanging requests.
- **D-SF03:** Different user-facing messages for safety block vs scanner failure — safety block explains risk category with revision hint, failure message says "Your message could not be processed due to a system error. Please try again later." Clear distinction for legitimate users; no system internals revealed to attackers.

### Audit Event Schema
- **D-AE01:** Comprehensive metadata fields: event_id (UUID), timestamp, user_id (UUID FK to users), model_id (TEXT), source (ENUM: input/output), risk_categories (JSON array), policy_action (ENUM: allow/block/fail-closed), scanner_findings_summary (JSON: anonymized PII types found, scanner names, not values).
- **D-AE02:** SQLAlchemy JSON type for risk_categories and scanner_findings — stored as TEXT in SQLite (aiosqlite), native JSONB in PostgreSQL when production switches. Same code works for both databases.

### Test Fixture Design
- **D-TF01:** Synthetic crafted samples — controlled, predictable triggers for each category. No risk of real sensitive data. E.g., "My SSN is 123-45-6789" for PII, "Ignore previous instructions" for prompt injection.
- **D-TF02:** All categories covered + safe/allowed content fixtures — ~15-20 fixtures total. Covers PII (SSN, email, phone, credit card, Chinese national ID), sensitive data (employee ID, project code), prompt injection, jailbreak, harmful content, unsafe model output, scanner failure, and safe/allowed content.
- **D-TF03:** Include Chinese-language fixtures for national ID testing — e.g., "我的身份证号码是110101199001011234" and mixed English+Chinese inputs. Validates custom recognizers work with real enterprise text patterns.

### Claude's Discretion
- Chat response shape (unified with status field vs distinct allowed/block shapes) — planner decides
- Exact Presidio recognizer enablement subset — researcher verifies compatibility with custom recognizers
- Exact LLM Guard scanner configuration parameters (thresholds, model weights) — researcher verifies
- DB migration for new audit_events table (column types, indexes, constraints) — planner decides
- Scanner timeout implementation (async cancellation mechanism) — planner decides
- Frontend chat page component structure and layout — planner decides

### Folded Todos
- **filter-library-selection.md**: Evaluate and select filtering libraries for DataProtectionScanner and LLMGuardrailScanner. Resolution: libraries already selected (Presidio for PII, LLM Guard for guardrails) per key-decisions.md and STACK.md. Carried forward as locked decision — no further evaluation needed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Definition
- `.planning/PROJECT.md` — Core value, constraints, key decisions, context
- `.planning/REQUIREMENTS.md` — SAFE-01 through SAFE-08, CHAT-01, CHAT-02, TEST-01 through TEST-05 mapped to this phase
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria, requirement mappings

### Research
- `.planning/research/STACK.md` — Presidio, LLM Guard, spaCy, httpx, openai SDK recommendations with versions, rationale, and installation commands
- `.planning/research/SUMMARY.md` — Research synthesis with roadmap implications

### Key Decisions
- `.planning/notes/key-decisions.md` — Mock OIDC strategy, Presidio + LLM Guard choice, conversation storage policy, local dev first

### Codebase Integration Points
- `backend/app/safety/pipeline.py` — SafetyPipeline placeholder to be replaced with real implementation
- `backend/app/safety/data_protection.py` — DataProtectionScanner placeholder to be replaced with Presidio-backed implementation
- `backend/app/safety/llm_guardrails.py` — LLMGuardrailScanner placeholder to be replaced with LLM Guard-backed implementation
- `backend/app/safety/policy.py` — SafetyPolicy placeholder to be replaced with real policy evaluation
- `backend/app/api/chat.py` — Chat endpoint placeholder with auth middleware integration
- `backend/app/models/providers.py` — ModelProvider interface stub to be replaced with ABC + implementations
- `backend/app/audit/events.py` — AuditEvent stub to be replaced with full model + DB table
- `backend/app/db/schema.py` — User and Session models (Phase 1 established), Base declarative class
- `backend/app/auth/current_user.py` — Auth middleware (get_current_user, get_admin_user)
- `frontend/src/lib/api.ts` — API client with AuthError handling
- `frontend/src/stores/authStore.ts` — Auth state store (user, role, session)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/auth/current_user.py` — `get_current_user` Depends for all authenticated endpoints, `get_admin_user` for admin-only routes. Phase 2 chat endpoints use `get_current_user`.
- `backend/app/db/schema.py` — `Base` declarative class, `User` model (id, email, name, role), `Session` model (id, user_id, token, expires_at). Established patterns for UUID columns via `Uuid` type and naive UTC timestamps. Phase 2 adds `audit_events` table to same schema.
- `frontend/src/lib/api.ts` — `apiClient<T>` with `AuthError` handling, `credentials: "include"` for session cookies. Phase 2 adds chat API calls using same client.
- `frontend/src/stores/authStore.ts` — Zustand auth state (user, role, session). Chat page reads auth state to verify authenticated user.

### Established Patterns
- SQLAlchemy 2 declarative mapping with `mapped_column`, UUID via `Uuid` type, naive UTC datetimes for DB compatibility across SQLite and PostgreSQL
- FastAPI `Depends` pattern for auth middleware — request-scoped dependency injection
- Server-side sessions in DB (SQLite/aiosqlite for MVP, PostgreSQL/asyncpg for production) — switch via `DATABASE_URL` in `.env`
- TanStack Query for frontend data fetching with 5-minute stale time, `AuthError` retry policy
- Zustand for client state management — minimal, TypeScript-first
- Vite proxy to backend at localhost:8000 for `/api` routes during development
- Phase 1 placeholder modules in `safety/`, `models/`, `audit/` directories — ready to fill with real implementations

### Integration Points
- `backend/app/api/chat.py` — New chat endpoints: POST `/api/chat/send` (message + model → response), GET `/api/chat/models` (available providers). Both require `Depends(get_current_user)`.
- `backend/app/safety/pipeline.py` — Replace placeholder with real `SafetyPipeline` that coordinates DataProtectionScanner + LLMGuardrailScanner, aggregates findings, and returns PolicyDecision.
- `backend/app/safety/data_protection.py` — Replace placeholder with Presidio-backed `DataProtectionScanner` using `presidio-analyzer` + `presidio-anonymizer` + custom recognizers.
- `backend/app/safety/llm_guardrails.py` — Replace placeholder with LLM Guard-backed `LLMGuardrailScanner` using `llm-guard` scanners.
- `backend/app/safety/policy.py` — Replace placeholder with `SafetyPolicy` that evaluates aggregated scanner findings and returns allow/block/fail-closed decision.
- `backend/app/models/providers.py` — Replace placeholder with `ModelProvider` ABC + `QwenProvider` (httpx to Qwen API) + `OpenAICompatibleProvider` (openai SDK with custom base_url).
- `backend/app/audit/events.py` — Replace placeholder with full `AuditEvent` model + SQLAlchemy table + repository for creating/querying events.
- `backend/app/db/schema.py` — Add `AuditEvent` table (event_id, timestamp, user_id, model_id, source, risk_categories JSON, policy_action, scanner_findings JSON). Use Alembic migration.
- `frontend/src/routes.tsx` — Add `/chat` route for new chat page component.
- `backend/app/main.py` — Include chat router and audit event creation in startup.

</code_context>

<specifics>
## Specific Ideas

- Block messages follow category-specific templates aligned with SAFE requirements (PII, sensitive data, prompt injection, jailbreak, harmful content, compliance) — each template has distinct wording for input vs output side, plus revision hint
- Input block: "Your message was blocked because it contains [category]. [Revision hint]. Please try again."
- Output block: "The response was blocked because it contains [category]. [Revision hint]. Please try again."
- Scanner failure: "Your message could not be processed due to a system error. Please try again later."
- Chat request shape: `{message: string, model_id: string}` — explicit model per request
- Model list response: `[{id: string, name: string, description: string}]`
- Chinese national ID recognizer validates checksum (last digit computed from first 17)
- NLP-enhanced custom recognizers use spaCy context words for detection accuracy
- 30-second pipeline timeout for fail-closed blocking
- Audit event stores anonymized findings (PII type labels, scanner names) — never raw values
- SQLAlchemy JSON type handles SQLite TEXT and PostgreSQL JSONB transparently

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 2-Safety Pipeline & Chat*
*Context gathered: 2026-05-21*