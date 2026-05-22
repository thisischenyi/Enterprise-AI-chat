# Phase 3: Conversation History & Chat Interface - Pattern Map

**Mapped:** 2026-05-22
**Files analyzed:** 8
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/db/schema.py` (modify) | model | CRUD | self — existing User/AuditEvent models | exact |
| `backend/alembic/versions/xxx_add_conversations.py` (new) | migration | — | No existing migrations (use alembic autogenerate) | no-analog |
| `backend/app/api/conversations.py` (new) | controller | CRUD | `backend/app/api/chat.py` | role-match |
| `backend/app/api/chat.py` (modify) | controller | request-response | self | exact |
| `backend/app/conversations/repository.py` (new) | service | CRUD | `backend/app/audit/repository.py` | exact |
| `frontend/src/lib/api.ts` (modify) | utility | request-response | self | exact |
| `frontend/src/features/chat/ChatPage.tsx` (modify) | component | request-response | self | exact |
| `frontend/src/features/chat/ConversationSidebar.tsx` (new) | component | CRUD | `frontend/src/features/chat/ChatPage.tsx` | role-match |
| `frontend/src/stores/chatStore.ts` (modify) | store | event-driven | self | exact |

## Pattern Assignments

### `backend/app/db/schema.py` — Add Conversation + Message models

**Analog:** Same file, existing models (lines 21-57)

**Model pattern:**
```python
import uuid
from datetime import datetime

from sqlalchemy import Index, JSON, String, ForeignKey, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    # ... follows same pattern as User/Session/AuditEvent
```

**Index pattern** (from AuditEvent, lines 46-49):
```python
__table_args__ = (
    Index("ix_messages_conversation_created", "conversation_id", "created_at"),
)
```

---

### `backend/app/api/conversations.py` — New CRUD endpoints

**Analog:** `backend/app/api/chat.py` (lines 1-27, 82-89)

**Imports pattern:**
```python
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.current_user import get_current_user
from app.db import get_db_session
from app.db.schema import User
```

**Router + auth pattern:**
```python
router = APIRouter()

@router.get("/")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    ...
```

**Response model pattern** (lines 39-45):
```python
class ConversationSummary(BaseModel):
    id: str
    title: str
    model_id: str
    updated_at: str
```

---

### `backend/app/api/chat.py` — Extend POST /send with conversation_id

**Analog:** Self (lines 82-163)

**Key modification points:**
- ChatRequest (line 34-36): add `conversation_id: str | None = None`
- ChatResponse (line 39-45): add `conversation_id: str | None = None`, `message_id: str | None = None`
- After output allowed (line 156-163): persist user + assistant messages, handle lazy conversation creation

---

### `backend/app/conversations/repository.py` — Conversation CRUD

**Analog:** `backend/app/audit/repository.py` (full file)

**Repository class pattern:**
```python
class ConversationRepository:
    """CRUD for conversations and messages."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_conversation(self, user_id: uuid.UUID, title: str, model_id: str) -> Conversation:
        conv = Conversation(id=uuid.uuid4(), user_id=user_id, title=title, model_id=model_id, ...)
        self._session.add(conv)
        await self._session.flush()
        return conv
```

**Query pattern** (SQLAlchemy 2 select style):
```python
from sqlalchemy import select

async def list_for_user(self, user_id: uuid.UUID) -> list[Conversation]:
    stmt = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())
    result = await self._session.execute(stmt)
    return list(result.scalars().all())
```

---

### `frontend/src/lib/api.ts` — Add conversation API functions

**Analog:** Self (lines 71-83)

**API function pattern:**
```typescript
export async function fetchConversations(): Promise<ConversationSummary[]> {
  return apiClient<ConversationSummary[]>("/conversations");
}

export async function fetchConversationMessages(id: string): Promise<MessageResponse[]> {
  return apiClient<MessageResponse[]>(`/conversations/${id}/messages`);
}
```

---

### `frontend/src/features/chat/ConversationSidebar.tsx` — New sidebar component

**Analog:** `frontend/src/features/chat/ChatPage.tsx` (full file)

**Component + TanStack Query pattern:**
```typescript
import { useQuery } from "@tanstack/react-query";
import { fetchConversations } from "../../lib/api";
import { useChatStore } from "../../stores/chatStore";

export default function ConversationSidebar() {
  const { data: conversations } = useQuery({
    queryKey: ["conversations"],
    queryFn: fetchConversations,
  });
  // ...
}
```

**Tailwind layout pattern** (from ChatPage line 71):
```typescript
<div className="flex h-screen flex-col">
```

---

### `frontend/src/features/chat/ChatPage.tsx` — Add sidebar layout

**Analog:** Self (lines 70-84)

**Layout modification:** Wrap existing content in flex-row with sidebar:
```typescript
return (
  <div className="flex h-screen">
    <ConversationSidebar />
    <div className="flex flex-1 flex-col">
      {/* existing content */}
    </div>
  </div>
);
```

---

### `frontend/src/stores/chatStore.ts` — Extend with conversation state

**Analog:** Self (full file)

**State extension pattern:**
```typescript
interface ChatState {
  // existing fields...
  activeConversationId: string | null;
  setActiveConversation: (id: string | null) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  // existing...
  activeConversationId: null,
  setActiveConversation: (id) => set({ activeConversationId: id, messages: [] }),
}));
```

## Shared Patterns

### Authentication (all backend endpoints)
**Source:** `backend/app/api/chat.py` line 85
**Apply to:** All new API endpoints in `conversations.py`
```python
current_user: User = Depends(get_current_user),
```

### Database Session Dependency
**Source:** `backend/app/api/chat.py` line 88
**Apply to:** All endpoints needing DB access
```python
db: AsyncSession = Depends(get_db_session),
```

### API Client (frontend)
**Source:** `frontend/src/lib/api.ts` lines 25-50
**Apply to:** All new API functions — use `apiClient<T>(path, options)` helper

### TanStack Query Pattern
**Source:** `frontend/src/features/chat/ChatPage.tsx` lines 13-18
**Apply to:** ConversationSidebar (useQuery), ChatPage send mutation (invalidate conversations)

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/alembic/versions/xxx_add_conversations.py` | migration | — | No existing migration files in repo. Use `alembic revision --autogenerate` to create. |

## Metadata

**Analog search scope:** `backend/app/`, `frontend/src/`
**Files scanned:** 8 source files read
**Pattern extraction date:** 2026-05-22
