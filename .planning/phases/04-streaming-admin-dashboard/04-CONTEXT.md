# Phase 4: Streaming & Admin Dashboard - Context

**Gathered:** 2026-05-22
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers two capabilities:
1. **Streaming chat responses** with sentence-based safety buffering and inline redaction (output only)
2. **Admin dashboard** for viewing audit events, configuring model providers, and managing safety policy thresholds

</domain>

<decisions>
## Implementation Decisions

### Streaming Safety Buffer
- **D-STR01:** Sliding window buffer with sentence-based chunks — accumulate tokens until sentence boundary (period/newline), safety-scan each sentence, release if safe
- **D-STR02:** Output uses inline redaction (NOT full-block) — sensitive sentences are replaced with `<REDACTED: PII>`, `<REDACTED: SECRET>`, `<REDACTED: POLICY>` placeholders. Input remains full-block per SAFE-03
- **D-STR03:** Full original model response stored in DB Messages table — redaction is display-only
- **D-STR04:** SSE transport with typed events: `chunk` (safe content), `redacted` (filtered content with risk category), `done`, `error`
- **D-STR05:** New endpoint POST /api/chat/stream — separate from existing /chat/send. Shared safety/persistence logic extracted to service layer
- **D-STR06:** Frontend auto-degrades to non-streaming (/chat/send) if SSE connection fails

### Streaming Render Experience
- **D-STR07:** Incremental append rendering (ChatGPT-style typing effect) — each chunk appended to message bubble as received
- **D-STR08:** Redacted content rendered as red background label tags (e.g. `[PII已过滤]`, `[POLICY违规已过滤]`) — visible but not disruptive

### Admin Audit Viewer
- **D-ADM01:** Layout: statistics cards (top) + filter bar + data table (below)
- **D-ADM02:** Statistics: 4-5 cards — today's total events, today's blocks, block rate %, most active user, plus 7-day trend mini-chart
- **D-ADM03:** Time range toggle: today / 7 days / 30 days — cards and table update together
- **D-ADM04:** Multi-dimension combined filter: time range, user, model, action (allow/block/fail_closed), risk category
- **D-ADM05:** Traditional pagination for data table (page numbers + prev/next)

### Admin Configuration UI
- **D-ADM06:** Configuration stored in database tables — supports runtime modification via API
- **D-ADM07:** Save button confirmation — changes not applied until user clicks Save
- **D-ADM08:** Sidebar navigation within admin: Audit Viewer / Model Config / Policy Config
- **D-ADM09:** Model provider config: card list with edit modal (name, endpoint, API key, enable/disable)
- **D-ADM10:** Policy/scanner config: scanner list with toggle switches (enable/disable) and sensitivity slider (low/medium/high)
- **D-ADM11:** API Key display: masked (****last4), encrypted storage in DB. Cannot view old value, only replace.

### Admin Route Structure
- **D-ADM12:** Nested routes under /admin/*: /admin/audit, /admin/models, /admin/policy. Sidebar is a fixed layout component.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Safety Pipeline
- `.planning/phases/02-safety-pipeline-chat/02-01-SUMMARY.md` — Scanner interfaces and implementations
- `.planning/phases/02-safety-pipeline-chat/02-02-SUMMARY.md` — SafetyPipeline, policy, audit infrastructure
- `backend/app/safety/pipeline.py` — Current non-streaming safety pipeline implementation
- `backend/app/safety/scanner_interface.py` — Scanner ABC and PolicyDecision model

### Chat & Conversation
- `backend/app/api/chat.py` — Current POST /chat/send implementation (to share logic with /stream)
- `backend/app/conversations/repository.py` — Conversation persistence (reused by streaming)

### Admin Infrastructure
- `backend/app/api/admin.py` — Existing admin route placeholder (get_admin_user dependency)
- `backend/app/auth/current_user.py` — get_admin_user for admin route protection

### Audit
- `backend/app/audit/repository.py` — AuditRepository (data source for audit viewer)
- `backend/app/audit/events.py` — AuditEvent model/schema

### UI Patterns
- `frontend/src/features/chat/ChatPage.tsx` — Existing chat layout (sidebar + chat area pattern)
- `frontend/src/features/chat/ConversationSidebar.tsx` — Sidebar component pattern (reuse for admin)
- `.planning/phases/03-conversation-history-chat/03-UI-SPEC.md` — UI design patterns established

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SafetyPipeline.scan_output()` — can be adapted for per-sentence streaming scan
- `AuditRepository` — ready to serve GET queries for audit viewer (needs list endpoint with pagination/filter)
- `get_admin_user` dependency — admin route protection already built
- `ProviderRegistry` — model provider registry (needs DB-backed config instead of hardcoded)
- `ConversationSidebar.tsx` — date grouping + list pattern reusable for admin sidebar nav

### Established Patterns
- FastAPI APIRouter with Depends() for auth + DB session
- Pydantic BaseModel for request/response schemas
- TanStack Query (useQuery/useMutation) for frontend data fetching
- Zustand for client state management
- Tailwind CSS utility classes for styling

### Integration Points
- `/api/chat/stream` shares safety pipeline + conversation persistence with `/api/chat/send`
- Admin audit GET endpoint reads from existing `audit_events` table
- Admin model config writes to new `model_configs` DB table (replaces hardcoded registry)
- Admin policy config writes to new `policy_configs` DB table (replaces hardcoded SafetyPolicy)
- Frontend ChatPage needs to switch from fetch-based send to EventSource-based stream

</code_context>

<specifics>
## Specific Ideas

- Redaction labels should be Chinese-friendly: `[PII已过滤]`, `[机密信息已过滤]`, `[策略违规已过滤]`
- Trend chart can be a simple SVG sparkline — no need for heavy charting library for MVP
- Admin sidebar should visually distinguish from chat sidebar (different color scheme or header)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-streaming-admin-dashboard*
*Context gathered: 2026-05-22*
