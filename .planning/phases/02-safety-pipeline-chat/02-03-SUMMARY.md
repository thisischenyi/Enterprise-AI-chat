---
phase: 02-safety-pipeline-chat
plan: 03
subsystem: chat-api-frontend
tags: [model-provider, chat-api, safety-pipeline, frontend, zustand]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [chat-endpoint, model-providers, chat-ui]
  affects: [frontend-routing, backend-api]
tech_stack:
  added: [openai-sdk, tenacity, httpx-provider]
  patterns: [provider-registry, safety-pipeline-integration, zustand-store, tanstack-mutation]
key_files:
  created:
    - frontend/src/stores/chatStore.ts
    - frontend/src/features/chat/ChatPage.tsx
    - frontend/src/features/chat/ModelSelector.tsx
    - frontend/src/features/chat/ChatMessages.tsx
    - frontend/src/features/chat/ChatInput.tsx
    - frontend/src/features/chat/BlockedMessage.tsx
  modified:
    - backend/app/models/providers.py
    - backend/app/models/qwen.py
    - backend/app/models/openai_compatible.py
    - backend/app/api/chat.py
    - backend/requirements.txt
    - backend/.env.example
    - frontend/src/lib/api.ts
    - frontend/src/routes.tsx
decisions:
  - "SafetyPipeline initialized with empty scanners list for MVP (scanners added when deps available)"
  - "ProviderRegistry created per-request via FastAPI Depends (lightweight, reads env vars)"
  - "Non-streaming mode for Phase 2 — stream=False in both providers"
metrics:
  duration: "5m"
  completed: "2026-05-22T16:01:26Z"
---

# Phase 02 Plan 03: Chat API + Model Providers + Frontend Summary

JWT-less chat flow: model provider ABC with Qwen (httpx) and OpenAI-compatible (openai SDK) implementations, POST /api/chat/send with full safety pipeline integration (input scan, model call, output scan, audit), GET /api/chat/models, and React /chat page with Zustand state and TanStack Query mutations.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | ModelProvider ABC + providers + registry | d5e9b64 | providers.py, qwen.py, openai_compatible.py |
| 2 | Chat API endpoints with safety pipeline | e3a8375 | api/chat.py |
| 3 | Frontend chat page + store + route | 6b723ee | ChatPage.tsx, chatStore.ts, routes.tsx |

## Deviations from Plan

None - plan executed exactly as written.

## Key Implementation Details

- **ModelProvider ABC**: Abstract base with `chat_completion(messages) -> str`. QwenProvider uses httpx with tenacity retry (3 attempts, exponential backoff). OpenAICompatibleProvider uses openai AsyncOpenAI SDK.
- **ProviderRegistry**: Checks QWEN_API_KEY and LOCAL_LLM_BASE_URL env vars to determine available providers.
- **POST /send flow**: Validates model_id -> input scan -> model call -> output scan -> audit event. Returns unified ChatResponse with status field.
- **Frontend**: Zustand store for chat state, TanStack Query mutation for send, useQuery for models. BlockedMessage shows risk categories as badges without echoing detected content.

## Self-Check: PASSED
