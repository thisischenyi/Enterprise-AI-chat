# Phase 4: Streaming & Admin Dashboard - Research

**Researched:** 2026-05-22
**Domain:** SSE streaming with safety buffering, admin CRUD dashboard
**Confidence:** HIGH

## Summary

This phase adds two capabilities: (1) streaming chat responses with sentence-based safety buffering and inline redaction, and (2) an admin dashboard for audit viewing, model config, and policy config. The existing codebase already has `sse-starlette` (just installed, v3.4.4) for backend SSE and `eventsource-parser` (v2.0.1) in frontend package.json. The safety pipeline (`SafetyPipeline.scan_output()`) needs adaptation to scan sentence-sized chunks instead of full responses. The admin dashboard is standard CRUD with TanStack Query + Tailwind, no new libraries needed.

**Primary recommendation:** Build streaming as a service layer that wraps the existing provider `chat_completion` with `stream=True`, buffers tokens into sentences, scans each sentence through `SafetyPipeline._scan()`, then emits typed SSE events. Admin dashboard is straightforward REST CRUD with the existing stack.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-STR01: Sliding window buffer with sentence-based chunks
- D-STR02: Output uses inline redaction (NOT full-block) for streaming output
- D-STR03: Full original model response stored in DB
- D-STR04: SSE transport with typed events: chunk, redacted, done, error
- D-STR05: New endpoint POST /api/chat/stream
- D-STR06: Frontend auto-degrades to non-streaming
- D-STR07: Incremental append rendering
- D-STR08: Redacted content rendered as red background label tags
- D-ADM01-12: Admin dashboard layout, audit viewer, config UI decisions

### Claude's Discretion
- Internal buffering implementation details
- Admin API endpoint naming/structure
- DB table schema for model_configs and policy_configs

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CHAT-03 | Chat responses stream with safety buffer preventing unsafe tokens from display | Streaming service layer with sentence buffering + sse-starlette SSE events |
| ADMN-01 | Admin can view audit event metadata through dashboard UI | GET /api/admin/audit with pagination/filter, existing AuditEvent table has all needed fields |
| ADMN-02 | Admin can configure model providers and credentials | New model_configs table + CRUD API + encrypted API key storage |
| ADMN-03 | Admin can configure policy thresholds and enabled scanner modules | New policy_configs table + CRUD API + scanner enable/disable + sensitivity levels |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SSE streaming + safety buffer | API / Backend | -- | All safety enforcement on backend per project constraint |
| Token accumulation + sentence detection | API / Backend | -- | Buffer logic lives in streaming service |
| Stream consumption + render | Browser / Client | -- | EventSource API + incremental DOM append |
| Auto-degrade to non-streaming | Browser / Client | -- | Frontend detects SSE failure, falls back to POST /send |
| Audit viewer (read) | Browser / Client | API / Backend | Frontend renders, backend serves paginated data |
| Model config CRUD | API / Backend | Database | Backend validates + encrypts keys, DB stores |
| Policy config CRUD | API / Backend | Database | Backend applies config to SafetyPolicy at runtime |

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sse-starlette | 3.4.4 | SSE responses from FastAPI | Standard SSE lib for Starlette/FastAPI [VERIFIED: pip install] |
| eventsource-parser | 2.0.1 | Parse SSE stream on frontend | Already in package.json [VERIFIED: package.json] |
| httpx | 0.28.x | Streaming HTTP client for model providers | Already installed, supports `stream=True` for SSE consumption [VERIFIED: requirements.txt] |

### New (no new packages needed)
No new packages required. All capabilities are covered by existing dependencies:
- SSE production: `sse-starlette`
- SSE consumption: `eventsource-parser`
- Streaming HTTP: `httpx` with `aiter_lines()`
- Admin CRUD: FastAPI + SQLAlchemy + TanStack Query (all installed)
- Encryption for API keys: Python stdlib `cryptography` or simple Fernet — but for MVP, base64 masking is sufficient per D-ADM11 (cannot view old value, only replace)

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sse-starlette | Raw StreamingResponse | SSE framing (event types, data lines) is error-prone to hand-roll |
| Sentence splitting with regex | spaCy sentence tokenizer | Regex on `.!?\n` is sufficient for MVP; spaCy adds latency per chunk |

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| sse-starlette | PyPI | ~5 yrs | established | github.com/sysid/sse-starlette | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none (eventsource-parser is npm, not PyPI — already in frontend package.json)
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture — Streaming Flow

```
User sends message
       |
       v
POST /api/chat/stream
       |
       v
[Input Safety Scan] --block--> SSE error event + audit
       |
       | allow
       v
[Model Provider stream=True] --> token stream
       |
       v
[Sentence Buffer] -- accumulates tokens until sentence boundary
       |
       v
[Output Safety Scan per sentence]
       |              |
       | safe         | unsafe
       v              v
SSE "chunk" event    SSE "redacted" event (category label)
       |
       v (when stream ends)
[Store full response in DB] --> SSE "done" event + audit
```

### Streaming Service Layer

```
backend/
├── app/
│   ├── api/
│   │   ├── chat.py          # Existing /send (unchanged)
│   │   ├── chat_stream.py   # NEW: POST /stream endpoint
│   │   └── admin.py         # EXPAND: audit, model, policy CRUD
│   ├── streaming/
│   │   ├── __init__.py
│   │   ├── buffer.py        # SentenceBuffer class
│   │   └── service.py       # StreamingChatService (orchestrates)
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── models_repo.py   # ModelConfig CRUD
│   │   └── policy_repo.py   # PolicyConfig CRUD
│   └── db/
│       └── schema.py        # ADD: ModelConfig, PolicyConfig tables
frontend/
├── src/
│   ├── features/
│   │   ├── chat/
│   │   │   └── useStreamChat.ts  # NEW: SSE hook replacing mutation
│   │   └── admin/
│   │       ├── AdminLayout.tsx    # Sidebar + outlet
│   │       ├── AuditPage.tsx      # Stats + filter + table
│   │       ├── ModelsPage.tsx     # Card grid + edit modal
│   │       └── PolicyPage.tsx     # Scanner toggles + sliders
│   └── lib/
│       └── api.ts           # ADD: admin API functions
```

### Pattern 1: Sentence Buffer

**What:** Accumulates streaming tokens, emits complete sentences for safety scanning.
**When to use:** Every streaming response.

```python
# [ASSUMED] — pattern based on training knowledge
import re

class SentenceBuffer:
    """Accumulates tokens, yields complete sentences."""

    SENTENCE_END = re.compile(r'[.!?\n]\s*$')

    def __init__(self) -> None:
        self._buffer = ""
        self._full_response = ""

    def add_token(self, token: str) -> list[str]:
        """Add token, return list of complete sentences (0 or more)."""
        self._buffer += token
        self._full_response += token
        sentences = []
        # Split on sentence boundaries
        while self.SENTENCE_END.search(self._buffer):
            match = self.SENTENCE_END.search(self._buffer)
            end_pos = match.end()
            sentences.append(self._buffer[:end_pos])
            self._buffer = self._buffer[end_pos:]
        return sentences

    def flush(self) -> str | None:
        """Flush remaining buffer (end of stream)."""
        if self._buffer.strip():
            remaining = self._buffer
            self._buffer = ""
            return remaining
        return None

    @property
    def full_response(self) -> str:
        return self._full_response
```

### Pattern 2: SSE Event Types

**What:** Typed SSE events matching D-STR04.

```python
# Backend SSE event emission
from sse_starlette.sse import EventSourceResponse

async def stream_generator():
    # ... buffering logic ...
    yield {"event": "chunk", "data": json.dumps({"content": safe_sentence})}
    yield {"event": "redacted", "data": json.dumps({"category": "PII", "label": "[PII已过滤]"})}
    yield {"event": "done", "data": json.dumps({"conversation_id": str(conv_id), "message_id": str(msg_id)})}
    yield {"event": "error", "data": json.dumps({"message": "..."})}
```

### Pattern 3: Frontend SSE Consumption

**What:** Use eventsource-parser to consume typed SSE events with auto-degrade.

```typescript
// [ASSUMED] — based on eventsource-parser v2 API from package.json
import { EventSourceParserStream } from "eventsource-parser/stream";

async function streamChat(message: string, modelId: string, conversationId?: string) {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, model_id: modelId, conversation_id: conversationId }),
  });

  if (!response.ok || !response.body) {
    // Auto-degrade to non-streaming
    return fallbackToSend(message, modelId, conversationId);
  }

  const stream = response.body
    .pipeThrough(new TextDecoderStream())
    .pipeThrough(new EventSourceParserStream());

  for await (const event of stream) {
    switch (event.event) {
      case "chunk":
        // Append safe content
        break;
      case "redacted":
        // Append redaction tag
        break;
      case "done":
        // Finalize message
        break;
      case "error":
        // Show error
        break;
    }
  }
}
```

### Anti-Patterns to Avoid
- **Scanning full accumulated response each time:** Only scan the new sentence, not the growing buffer. Otherwise O(n^2) safety scanning.
- **Streaming tokens directly to frontend before safety scan:** Violates the core safety guarantee. Always buffer-then-scan-then-emit.
- **Creating new AsyncClient per streaming request:** Reuse httpx client with connection pooling.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE framing | Manual "data: ...\n\n" formatting | sse-starlette EventSourceResponse | Event types, retry, keep-alive handled |
| SSE parsing (frontend) | Manual text splitting on "data:" | eventsource-parser | Handles multi-line data, reconnection IDs |
| Pagination | Custom offset/limit logic | SQLAlchemy `.offset().limit()` + count query | Standard, tested, handles edge cases |

## Common Pitfalls

### Pitfall 1: Sentence boundary in middle of token
**What goes wrong:** Model emits "Dr." and buffer thinks it's a sentence end.
**Why it happens:** Simple regex splits on any period.
**How to avoid:** Use `\n` as primary boundary, period only when followed by space+uppercase or double-newline. Keep regex simple but slightly smarter than bare `.`.
**Warning signs:** Short nonsensical "sentences" being safety-scanned.

### Pitfall 2: SSE connection drops without "done" event
**What goes wrong:** Frontend hangs waiting for done event that never arrives.
**Why it happens:** Network interruption, server crash, timeout.
**How to avoid:** Frontend sets a timeout (e.g., 60s since last event). On timeout, auto-degrade per D-STR06.
**Warning signs:** Spinning indicators that never resolve.

### Pitfall 3: Forgetting to store full response in DB
**What goes wrong:** Only redacted version gets stored, losing original per D-STR03.
**Why it happens:** Developer stores after redaction instead of accumulating full_response separately.
**How to avoid:** SentenceBuffer.full_response property accumulates everything; store THAT in DB at stream end.
**Warning signs:** DB content has redaction placeholders.

### Pitfall 4: Admin API key exposure in responses
**What goes wrong:** GET /admin/models returns decrypted API keys.
**Why it happens:** Serializing the full DB model without field exclusion.
**How to avoid:** Response schema explicitly masks: `api_key = "****" + last4`. Never include full key in any response.
**Warning signs:** API keys visible in browser network tab.

## Code Examples

### Streaming Endpoint Structure

```python
# backend/app/api/chat_stream.py
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    pipeline: SafetyPipeline = Depends(get_safety_pipeline),
    registry: ProviderRegistry = Depends(get_provider_registry),
    db: AsyncSession = Depends(get_db_session),
) -> EventSourceResponse:
    # Input scan first (non-streaming, same as /send)
    input_decision = await pipeline.scan_input(request.message, user_id, request.model_id)
    if input_decision.action != "allow":
        # Return error SSE event immediately
        return EventSourceResponse(error_generator(input_decision))

    return EventSourceResponse(stream_with_safety(request, user_id, pipeline, provider, db))
```

### Admin Audit Query with Filters

```python
# backend/app/admin/audit_queries.py
async def list_audit_events(
    session: AsyncSession,
    time_range: str = "today",  # today | 7d | 30d
    user_id: uuid.UUID | None = None,
    model_id: str | None = None,
    action: str | None = None,
    risk_category: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AuditEvent], int]:
    query = select(AuditEvent)
    # Apply filters...
    count = await session.scalar(select(func.count()).select_from(query.subquery()))
    results = await session.scalars(query.offset((page-1)*page_size).limit(page_size))
    return list(results), count
```

## New Database Tables

```python
# ModelConfig table
class ModelConfig(Base):
    __tablename__ = "model_configs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "qwen" | "openai_compatible"
    endpoint_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

# PolicyConfig table
class PolicyConfig(Base):
    __tablename__ = "policy_configs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    scanner_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    sensitivity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")  # low|medium|high
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WebSocket for streaming | SSE (Server-Sent Events) | 2023+ | SSE is simpler, unidirectional (server->client), works with HTTP/2, no upgrade handshake |
| Full response then display | Token streaming with buffer | ChatGPT popularized 2023 | User perceives faster response, but safety requires buffering |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | eventsource-parser v2 exports EventSourceParserStream for web streams API | Code Examples | Would need different import/API — check docs |
| A2 | sse-starlette EventSourceResponse accepts async generator yielding dicts with "event" and "data" keys | Code Examples | May need different yield format |
| A3 | Simple regex sentence splitting is adequate for MVP | Patterns | May need refinement if models produce unusual punctuation |

## Open Questions (RESOLVED)

1. **Model provider streaming API format** — RESOLVED
   - Resolution: Use OpenAI-compatible SSE format (`data: {"choices":[{"delta":{"content":"..."}}]}`). Set `stream: True` in httpx request, parse with `aiter_lines()`. Confirmed by Qwen/DashScope docs compatibility.

2. **API key encryption for MVP** — RESOLVED
   - Resolution: Use `cryptography.fernet` with app-level `ENCRYPTION_KEY` env var. Reversible encryption needed since keys must be decrypted for API calls. Store encrypted blob + last4 plaintext for display masking.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio (backend), Vitest 4.x (frontend) |
| Config file | backend: pytest.ini or pyproject.toml, frontend: vitest in vite.config |
| Quick run command | `pytest tests/ -x -q` / `npm run test` |
| Full suite command | `pytest tests/` / `npm run test` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| CHAT-03 | Stream with safety buffer | integration | `pytest tests/test_chat_stream.py -x` |
| ADMN-01 | Audit viewer API | unit | `pytest tests/test_admin_audit.py -x` |
| ADMN-02 | Model config CRUD | unit | `pytest tests/test_admin_models.py -x` |
| ADMN-03 | Policy config CRUD | unit | `pytest tests/test_admin_policy.py -x` |

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing get_admin_user dependency (403 for non-admin) |
| V4 Access Control | yes | Admin routes behind role check; model API keys never exposed |
| V5 Input Validation | yes | Pydantic schemas for all admin CRUD inputs |
| V6 Cryptography | yes | Fernet encryption for stored API keys |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| API key leakage in responses | Information Disclosure | Mask in serialization, never return full key |
| Non-admin accessing admin routes | Elevation of Privilege | get_admin_user dependency on all admin endpoints |
| SSE event injection | Tampering | Server-only event emission, no user content in event field names |

## Sources

### Primary (HIGH confidence)
- Codebase: backend/app/api/chat.py, backend/app/safety/pipeline.py, frontend/package.json
- slopcheck verification: sse-starlette [OK] on PyPI

### Secondary (MEDIUM confidence)
- sse-starlette usage patterns [ASSUMED from training data]
- eventsource-parser v2 API [ASSUMED from training data]

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all packages already installed and verified
- Architecture: HIGH - clear extension of existing patterns
- Pitfalls: MEDIUM - streaming edge cases from training knowledge

**Research date:** 2026-05-22
**Valid until:** 2026-06-22 (stable domain, no fast-moving deps)
