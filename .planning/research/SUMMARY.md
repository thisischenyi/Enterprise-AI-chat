# Project Research Summary

**Project:** Enterprise AI Chat MVP
**Domain:** Enterprise AI chat with safety filtering
**Researched:** 2026-05-21
**Confidence:** MEDIUM

## Executive Summary

Enterprise AI chat with safety filtering is a backend-gated pipeline architecture where all model calls and safety enforcement happen server-side. The frontend never contacts model providers directly — this is the only architecture that can guarantee safety policy compliance. The recommended approach is safety-first: build the input/output filtering pipeline before integrating any model providers, so safety is architecturally embedded, not bolted on.

The hardest technical problem is streaming with safety buffering — naive streaming leaks unsafe content before the scanner finishes. This requires a chunked buffer that accumulates streaming tokens until thresholds are met, then flushes safe content to the frontend. Start with non-streaming responses in the first chat phase, add buffered streaming in a later phase.

The biggest risks are: (1) streaming buffer bypass allowing unsafe tokens to reach the frontend, (2) scanner failure defaulting to allow instead of block, and (3) echoing PII in block messages. All three must be addressed in the safety pipeline architecture from day one.

## Key Findings

### Recommended Stack

The project docs specify React+TypeScript, Python+FastAPI, and PostgreSQL. Research fills in specific library choices and recommends streaming/SSE infrastructure, state management, and filtering libraries.

**Core technologies:**
- **React + TypeScript + Vite**: Frontend framework — Vite for fast dev server and builds, React for component architecture
- **FastAPI + SQLAlchemy 2 + asyncpg**: Backend framework — async I/O for streaming, SQLAlchemy for DB models
- **Microsoft Presidio**: PII detection and data classification — only mature open-source PII library with custom recognizer support, MIT license
- **ProtectAI LLM Guard**: Jailbreak, prompt injection, harmful content, compliance — Python library (no separate model server), covers all required scanner categories
- **sse-starlette**: SSE streaming for FastAPI — standard server-sent events implementation
- **Authlib**: OIDC client — standard OIDC integration library, used when real enterprise IDP is confirmed
- **itsdangerous**: Mock OIDC session tokens for MVP — simple token signing with fixed test user

### Expected Features

**Must have (table stakes):**
- OIDC authentication (mock for MVP) — users must be authenticated before any chat access
- Chat UI with model selection — select Qwen or local OpenAI-compatible model
- Input safety filtering — PII, sensitive data, prompt injection, jailbreak, harmful content detection before model call
- Output safety filtering — same checks on model responses before display
- Block/allow messages — clear explanation without echoing sensitive content
- Audit logging metadata — event ID, timestamp, user, model, risk categories, policy action, no raw content
- Conversation history — browse and resume past conversations (allowed-through content only)
- Streaming with safety buffer — responsive UX while maintaining safety guarantees
- Admin model/policy configuration — configure providers, credentials, scanner thresholds

**Should have (competitive):**
- Non-echoing block messages — compliance advantage, no secondary PII leak
- Data classification-aware filtering — enterprise-specific policy enforcement
- Safe conversation storage model — database never contains blocked content

**Defer (v2+):**
- Real OIDC integration — when enterprise confirms IDP provider
- Llama Guard 3 model — separate inference server, defer from MVP
- Advanced analytics dashboards — beyond audit viewer
- Fine-grained RBAC — employee/admin sufficient for MVP

### Architecture Approach

Backend-gated pipeline architecture with scanner interface abstraction. All safety enforcement happens at a single backend gateway. Scanners are wrapped behind a common `Scanner` protocol enabling swappable implementations without changing pipeline internals. Safety pipeline MUST exist before model calls — it is the only path to model providers.

**Major components:**
1. **Auth middleware** — OIDC (mock) session validation, user identity extraction, role (employee/admin)
2. **Safety pipeline** — Scanner interfaces (DataProtectionScanner, LLMGuardrailScanner), PolicyDecision engine, streaming buffer
3. **Model gateway** — Provider interface (QwenProvider, OpenAICompatibleProvider), chat completion routing
4. **Audit service** — Event recording, metadata-only storage, query API for admin dashboard
5. **Conversation store** — PostgreSQL persistence for allowed-through content only, conversation list and resume
6. **Admin API** — Model config, policy config, credential management, audit query endpoints

### Critical Pitfalls

1. **Streaming buffer bypass** — Unsafe tokens reach frontend before scanner finishes. Requires buffer-after-scan architecture from day one. Never flush tokens before safety check completes.
2. **Scanner failure defaulting to allow** — If Presidio/Llama Guard crashes, timeouts, or errors, content passes unfiltered. Must default to BLOCK (fail-closed, like a firewall).
3. **Echoing PII in block messages** — Block explanations that include detected SSN/phone become secondary PII leak. PolicyDecision must never carry raw entity text.
4. **Presidio missing enterprise-specific PII** — Default recognizers miss employee IDs, project codes, Chinese national IDs. Custom recognizers are mandatory, not optional.
5. **Scanner running on partial/truncated content** — PII and harmful content split across chunk boundaries are systematically missed. Requires overlap/sliding-window in output scanner buffer.

## Implications for Roadmap

Based on research, suggested phase structure (coarse granularity, 4-5 phases):

### Phase 1: Foundation & Auth
**Rationale:** Every endpoint depends on authentication. Project skeleton and DB schema must exist before safety pipeline.
**Delivers:** FastAPI + React project skeletons, PostgreSQL schema, mock OIDC auth middleware, DB migrations
**Addresses:** OIDC authentication requirement
**Avoids:** Late auth integration causing bypass paths

### Phase 2: Safety Pipeline & Model Gateway
**Rationale:** Safety-first architecture — pipeline must exist before any model calls. This is the core value prop.
**Delivers:** Scanner interfaces, Presidio + LLM Guard implementations, safety pipeline, PolicyDecision engine, model provider interfaces, non-streaming chat endpoint
**Uses:** Presidio, LLM Guard, FastAPI, SQLAlchemy
**Implements:** Safety pipeline + model gateway components
**Addresses:** Input/output filtering, block messages, audit logging, model selection
**Avoids:** 5 of 6 critical pitfalls (streaming bypass addressed architecturally, fail-closed semantics, non-echoing PolicyDecision, overlap window design, audit metadata schema)

### Phase 3: Chat UX & Conversation History
**Rationale:** Chat UI and conversation history can be built once the safety pipeline works end-to-end.
**Delivers:** Chat interface with model selection, conversation list/resume UI, allowed-through content storage, message display with block message UI
**Uses:** React, TanStack Query, Zustand, SSE client
**Addresses:** Chat UX, conversation history, block message display

### Phase 4: Streaming Safety Buffer & Admin Dashboard
**Rationale:** Streaming buffer is architecturally complex — build after core pipeline is proven. Admin dashboard is a parallel track.
**Delivers:** SSE streaming with safety buffer layer, admin dashboard UI (model config, policy config, audit viewer)
**Uses:** sse-starlette, streaming buffer architecture, React admin pages
**Addresses:** Streaming UX, admin model/policy configuration, admin audit viewer
**Avoids:** Streaming buffer bypass pitfall with proper buffer-after-scan architecture

### Phase Ordering Rationale

- **Safety pipeline before model integration** — If model integration is built first, safety gets bolted on later and bypass paths emerge. Safety is the core value, not an add-on.
- **Auth first, everything else depends on it** — Every API endpoint needs authenticated user identity for audit events and policy enforcement.
- **Non-streaming before streaming** — Get core pipeline working with simple request/response before adding streaming buffer complexity.
- **Chat UX after pipeline** — Frontend needs a working backend endpoint to build against. Pipeline must produce correct block/allow responses first.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** Complex integration — Presidio custom recognizers, LLM Guard scanner module selection, streaming buffer architecture needs detailed design
- **Phase 4:** Streaming buffer tuning — window sizes, latency vs safety trade-offs, SSE implementation details in FastAPI

Phases with standard patterns (skip research-phase):
- **Phase 1:** Standard FastAPI + React + PostgreSQL project scaffold, well-documented patterns
- **Phase 3:** Standard chat UI patterns, well-established React component patterns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Library selections well-justified; version numbers need verification against current docs |
| Features | MEDIUM | Table stakes well-established; differentiators need live market verification |
| Architecture | MEDIUM | Backend-gated pipeline is standard; streaming buffer details need implementation-specific research |
| Pitfalls | MEDIUM | Critical pitfalls are architectural (HIGH confidence); library-specific pitfalls need version verification |

**Overall confidence:** MEDIUM

### Gaps to Address

- **Version verification:** Run `pip index versions <pkg>` and `npm info <pkg> version` before pinning dependencies
- **LLM Guard scanner module selection:** Which specific scanners and thresholds for enterprise policy — needs enterprise policy input
- **Streaming buffer tuning:** Window size, check interval, latency trade-offs — needs Phase 4 implementation research
- **Presidio custom recognizers:** Enterprise-specific PII types (employee IDs, project codes, Chinese national IDs) — needs enterprise policy input
- **Real OIDC provider:** Enterprise must confirm IDP type and configuration — triggers oidc-provider-integration seed

## Sources

### Primary (HIGH confidence)
- SPEC.md — project requirements, tech stack, core flow, boundaries
- PROJECT.md — project context, constraints, key decisions
- .planning/notes/key-decisions.md — resolved open questions from SPEC

### Secondary (MEDIUM confidence)
- Research agent findings — STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md
- Industry patterns — backend-gated safety pipeline, streaming buffer architecture, fail-closed scanner semantics

### Tertiary (LOW confidence)
- Specific library version numbers — need pip/npm verification
- Llama Guard 3 vs LLM Guard performance comparison — needs benchmarking
- Qwen API streaming format — needs SDK documentation review

---
*Research completed: 2026-05-21*
*Ready for roadmap: yes*