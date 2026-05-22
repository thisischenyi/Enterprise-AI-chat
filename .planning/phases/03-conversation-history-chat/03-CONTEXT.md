# Phase 3: Conversation History & Chat Interface - Context

**Gathered:** 2026-05-22
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers conversation persistence and browsing:
- Conversation and Message data models with proper schema
- Conversation list sidebar integrated into existing /chat page
- Resume past conversations with full message history display
- Storage boundary enforcement: only allowed-through content stored
- Chat history sent as model context for coherent multi-turn conversations
- Auto-generated conversation titles from first message

This phase does NOT deliver: streaming responses (Phase 4), admin dashboard (Phase 4), message editing/deletion, search/filtering conversations.

</domain>

<decisions>
## Implementation Decisions

### Conversation Data Model
- **D-DM01:** Two-table design: Conversation (id, user_id, title, model_id, created_at, updated_at) + Message (id, conversation_id, role enum user/assistant, content, created_at). Standard normalized chat schema.
- **D-DM02:** Auto-title from first user message — truncate to ~50 characters. No user-editable title for MVP. Simplifies UI, avoids title input flow.
- **D-DM03:** Conversation.updated_at tracks last message timestamp for sorting in sidebar.

### Conversation List UI
- **D-UI01:** Sidebar on the existing /chat page — classic chat app layout (conversation list left, active chat right). Stays on /chat route. No separate /conversations page.
- **D-UI02:** Sidebar items show: title + relative date (Today, Yesterday, May 20). No preview snippet. Clean and scannable.
- **D-UI03:** "New conversation" button at top of sidebar. Clicking creates a fresh chat context (no DB row until first allowed message).

### Storage Boundary Enforcement
- **D-SB01:** API-level gate — chat API checks pipeline result. If blocked: write audit event, return block_message to frontend, never write to Message table. Clean separation.
- **D-SB02:** Lazy conversation creation — Conversation row created only on first allowed message. If user's first message is blocked, no conversation record exists. Prevents empty/orphan conversations.
- **D-SB03:** HIST-04 enforcement: blocked messages produce AuditEvent rows only. No Message rows. Existing audit infrastructure from Phase 2 handles this.

### Resume Conversation Behavior
- **D-RC01:** Full history load on resume — load all messages for a conversation. Simple for MVP with typically short conversations. No pagination needed yet.
- **D-RC02:** Model context: send last 20 messages as context to model provider when user sends a new message. Keeps conversations coherent without excessive token usage.
- **D-RC03:** Messages sent to model as standard chat format: [{role: "user", content: "..."}, {role: "assistant", content: "..."}, ...] — the format expected by both Qwen and OpenAI-compatible providers.

### Claude's Discretion
- Exact sidebar width and responsive breakpoint behavior
- Conversation list sort order (most recent first is the natural default)
- Empty state UI when user has no conversations
- How to handle very long titles (CSS truncation approach)
- Alembic migration details (indexes, constraints)
- Whether to add a "delete conversation" option in MVP

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Definition
- `.planning/PROJECT.md` — core value, constraints, requirements overview
- `.planning/REQUIREMENTS.md` — HIST-01 through HIST-04 definitions

### Prior Phase Context
- `.planning/phases/02-safety-pipeline-chat/02-CONTEXT.md` — D-CF01 through D-CF04 chat flow decisions, D-AE01/02 audit schema
- `.planning/phases/02-safety-pipeline-chat/02-01-SUMMARY.md` — scanner interface types
- `.planning/phases/02-safety-pipeline-chat/02-02-SUMMARY.md` — pipeline + audit architecture
- `.planning/phases/02-safety-pipeline-chat/02-03-SUMMARY.md` — model providers + chat API + frontend

### Existing Code (key integration points)
- `backend/app/api/chat.py` — existing POST /api/chat/send to extend with conversation persistence
- `backend/app/db/schema.py` — existing User, Session tables to extend with Conversation, Message
- `backend/app/models/providers.py` — ModelProvider.chat_completion() signature (needs messages list)
- `frontend/src/features/chat/ChatPage.tsx` — existing chat page to add sidebar to
- `frontend/src/stores/chatStore.ts` — existing Zustand store to extend with conversation state

### Technology Stack
- `.planning/research/STACK.md` — SQLAlchemy 2.x async, Alembic migrations, React Router 7, TanStack Query, Zustand

</canonical_refs>

<specifics>
## Specific Ideas

- Chat API already returns `{status: "allowed"|"blocked"|"fail_closed", message?, block_message?}` — extend to include `conversation_id` and `message_id` in allowed responses
- Existing `get_db_session` FastAPI dependency already available for all endpoints
- Phase 2's ModelProvider.chat_completion() currently takes a single prompt string — needs to accept messages list for multi-turn
- Frontend already has TanStack Query pattern from Phase 2 — use same pattern for conversation list and message fetching

</specifics>

<deferred>
## Deferred Ideas

- Message search/filtering across conversations — future phase
- Conversation sharing between users — future phase
- Export conversation as PDF/text — future phase
- Conversation folders/tags/pinning — future phase

</deferred>

---

*Phase: 03-conversation-history-chat*
*Context gathered: 2026-05-22 via discuss-phase*
