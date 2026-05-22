# Phase 3: Conversation History & Chat Interface - Research

**Researched:** 2026-05-22
**Domain:** Conversation persistence, chat UI patterns, SQLAlchemy async
**Confidence:** HIGH

## Summary

This phase adds conversation persistence and browsing to an existing working chat system. The existing code already supports multi-turn messages at the provider level (`chat_completion(messages: list[dict[str, str]])`), so the main work is: (1) two new DB tables with Alembic migration, (2) extending the chat API to persist allowed messages and accept conversation context, (3) new API endpoints for listing/fetching conversations, (4) frontend sidebar + conversation state management.

The technical risk is low — this is standard CRUD with a sidebar UI pattern. The key correctness concern is the storage boundary: ensuring blocked messages never create Message rows.

**Primary recommendation:** Implement backend-first (schema + migration + API), then frontend (sidebar + state refactor). Keep lazy conversation creation logic in the chat_send endpoint.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-DM01: Two-table design: Conversation (id, user_id, title, model_id, created_at, updated_at) + Message (id, conversation_id, role enum user/assistant, content, created_at)
- D-DM02: Auto-title from first user message, truncate ~50 chars, no user-editable title
- D-DM03: Conversation.updated_at tracks last message for sidebar sorting
- D-UI01: Sidebar on existing /chat page, classic chat layout
- D-UI02: Sidebar items show title + relative date, no preview snippet
- D-UI03: "New conversation" button at top, no DB row until first allowed message
- D-SB01: API-level gate — blocked messages never written to Message table
- D-SB02: Lazy conversation creation — row only on first allowed message
- D-SB03: Blocked messages produce AuditEvent rows only
- D-RC01: Full history load on resume (no pagination for MVP)
- D-RC02: Send last 20 messages as model context
- D-RC03: Standard chat format [{role, content}] for model calls

### Claude's Discretion
- Sidebar width and responsive breakpoints
- Sort order (most recent first)
- Empty state UI
- Long title handling (CSS truncation)
- Alembic migration details (indexes, constraints)
- Whether to add "delete conversation" in MVP

### Deferred Ideas (OUT OF SCOPE)
- Message search/filtering
- Conversation sharing
- Export as PDF/text
- Folders/tags/pinning
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HIST-01 | Browse list of past conversations | Conversation table + GET /conversations endpoint + sidebar UI |
| HIST-02 | Resume past conversation and continue chatting | GET /conversations/:id/messages + send with conversation_id context |
| HIST-03 | Store only allowed-through content | Storage gate in chat_send — persist only when pipeline allows |
| HIST-04 | Blocked messages generate audit events but no Message rows | Existing audit infra from Phase 2 + no Message write on block path |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Conversation persistence | Database / Backend | — | SQLAlchemy models, Alembic migration |
| Storage boundary enforcement | API / Backend | — | Gate logic lives in chat_send endpoint |
| Conversation list display | Frontend (Client) | API | TanStack Query fetches from backend |
| Multi-turn context assembly | API / Backend | — | Backend assembles last-20 messages before model call |
| Sidebar UI | Frontend (Client) | — | React component with Zustand state |

## Standard Stack

No new packages needed. This phase uses existing stack:
- SQLAlchemy 2.x async (already installed) — new models + queries
- Alembic (already installed) — migration for new tables
- TanStack Query (already installed) — conversation list/detail fetching
- Zustand (already installed) — extend chatStore with active conversation state

## Architecture Patterns

### Data Flow

```
User clicks conversation → GET /conversations/:id/messages → Frontend loads history
User sends message → POST /chat/send {message, model_id, conversation_id?}
  → Input safety scan
  → If blocked: audit event only, return block response
  → If allowed + no conversation_id: CREATE Conversation row, set title
  → CREATE Message(role=user)
  → Call model with last 20 messages as context
  → Output safety scan
  → If output blocked: audit event, return block (user message already stored — acceptable)
  → CREATE Message(role=assistant)
  → Return {status, content, conversation_id, message_id}
```

### Schema Design

```python
class Conversation(Base):
    __tablename__ = "conversations"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
```

### API Endpoints to Add

```
GET  /api/conversations          — list user's conversations (sorted by updated_at desc)
GET  /api/conversations/:id/messages — all messages for a conversation
POST /api/chat/send              — extend: accept optional conversation_id, return conversation_id
```

### Frontend State Extension

```typescript
// Extend chatStore
interface ChatState {
  // existing...
  activeConversationId: string | null;
  setActiveConversation: (id: string | null) => void;
  // messages now represent active conversation's messages
}
```

Use TanStack Query for:
- `useQuery(['conversations'])` — sidebar list
- `useQuery(['conversations', id, 'messages'])` — load on resume
- Invalidate conversation list after successful send

### Sidebar Component Structure

```
ChatPage (flex row)
├── ConversationSidebar (w-64, border-r)
│   ├── NewConversationButton
│   └── ConversationList
│       └── ConversationItem (title + relative date)
└── ChatMain (flex-1, existing layout)
    ├── ModelSelector header
    ├── ChatMessages
    └── ChatInput
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative date formatting | Custom date logic | `Intl.RelativeTimeFormat` or simple helper | Edge cases with timezones |
| Optimistic updates | Manual state sync | TanStack Query mutation + invalidation | Race conditions |

## Common Pitfalls

### Pitfall 1: Output Block After User Message Stored
**What goes wrong:** User message is persisted, then model output is blocked. Conversation has a dangling user message with no response.
**How to avoid:** This is acceptable for MVP — the user can see their message and the block notification. The block message is shown in UI but not stored. Document this as expected behavior.

### Pitfall 2: Race Condition on Lazy Conversation Creation
**What goes wrong:** Two rapid sends could both try to create a conversation.
**How to avoid:** Frontend disables input while send is in-flight (already done via isLoading). Backend: first allowed message in a send creates the conversation atomically.

### Pitfall 3: Stale Sidebar After New Message
**What goes wrong:** Sidebar doesn't update after sending a message in active conversation.
**How to avoid:** Invalidate the conversations query on successful send mutation.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Alembic is already configured with a migrations directory | Architecture | Need to set up alembic init first |

## Open Questions

1. **Output blocked — keep user message?**
   - Decision D-SB01 says "blocked: never write to Message table" — but this refers to the blocked content itself. If input passes but output is blocked, the user's allowed message is already stored. This seems correct (user message was allowed). Planner should confirm this interpretation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages, existing tools
- Architecture: HIGH — standard CRUD + sidebar pattern, existing code is clear
- Pitfalls: HIGH — well-understood domain

**Research date:** 2026-05-22
**Valid until:** 2026-06-22 (stable patterns, no moving targets)
