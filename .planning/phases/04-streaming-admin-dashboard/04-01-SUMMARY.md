---
phase: "04"
plan: "01"
subsystem: "streaming"
tags: [sse, streaming, safety-buffer, redaction]
dependency_graph:
  requires: [safety-pipeline, chat-api, conversations-repo, provider-registry]
  provides: [streaming-endpoint, sse-consumption-hook, streaming-message-component]
  affects: [ChatPage, main.py]
tech_stack:
  added: [sse-starlette, eventsource-parser/stream]
  patterns: [sentence-buffered-safety, auto-degrade-fallback]
key_files:
  created:
    - backend/app/streaming/__init__.py
    - backend/app/streaming/buffer.py
    - backend/app/streaming/service.py
    - backend/app/api/chat_stream.py
    - frontend/src/features/chat/useStreamChat.ts
    - frontend/src/features/chat/StreamingMessage.tsx
  modified:
    - backend/app/main.py
    - frontend/src/features/chat/ChatPage.tsx
decisions:
  - "Used non-streaming model call + sentence buffer (providers lack stream=True yet)"
  - "Redaction labels in Chinese matching UI-SPEC"
metrics:
  duration: "~8min"
  completed: "2026-05-22"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 04 Plan 01: Streaming Chat with Safety Buffering Summary

SSE streaming endpoint with sentence-level safety scanning and Chinese redaction labels, plus frontend hook with auto-degrade fallback.

## What Was Built

1. **SentenceBuffer** (`backend/app/streaming/buffer.py`) — accumulates tokens, splits on sentence boundaries (period/!/? + whitespace, newlines), exposes `full_response` for unredacted DB storage.

2. **StreamingChatService** (`backend/app/streaming/service.py`) — orchestrates: input safety scan, model call, per-sentence output scan, emits chunk/redacted/done/error events. Stores full unredacted response in DB.

3. **POST /api/chat/stream** (`backend/app/api/chat_stream.py`) — FastAPI endpoint returning `EventSourceResponse` wrapping the service generator.

4. **useStreamChat hook** (`frontend/src/features/chat/useStreamChat.ts`) — fetch + EventSourceParserStream consumption, 30s timeout, auto-degrade to `/api/chat/send`.

5. **StreamingMessage component** (`frontend/src/features/chat/StreamingMessage.tsx`) — renders text segments + redaction tags (`bg-red-50 text-red-700`), blinking cursor during stream.

6. **ChatPage integration** — streaming is primary send mechanism, degrade notice shown in Chinese.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 44644b1 | Backend streaming service + buffer + endpoint |
| 2 | 7a0804a | Frontend SSE hook + StreamingMessage + ChatPage |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SentenceBuffer regex consumed delimiter but not trailing whitespace**
- Found during: Task 1 verification
- Issue: Lookahead `(?=\s)` meant trailing space was left at start of next sentence
- Fix: Changed regex to consume punctuation + whitespace together
- Files modified: backend/app/streaming/buffer.py

### Design Decisions

- Providers do not yet support `stream=True`, so StreamingChatService calls `chat_completion` non-streaming and feeds full response through the sentence buffer. This delivers correct sentence-level safety scanning; true token streaming is a future enhancement when providers add streaming support.

## Known Stubs

None — all data paths are wired to real pipeline/provider/DB calls.

## Self-Check: PASSED
