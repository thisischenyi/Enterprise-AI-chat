<!-- GSD:project-start source:PROJECT.md -->
## Project

**Enterprise AI Chat MVP**

An enterprise AI chat web application that lets authenticated employees chat with approved LLMs (Alibaba Bailian Qwen and local OpenAI-compatible models) while enforcing input and output safety controls. The MVP is a demo prototype to prove that AI chat can be used safely in an enterprise environment — blocking sensitive content before model calls and blocking unsafe model responses before display.

Primary users are internal employees. Admin users configure models, policies, and view audit metadata.

**Core Value:** Prove that employees can use AI chat safely in a controlled enterprise environment — the safety pipeline (input filtering → model call → output filtering) must work reliably and block sensitive or non-compliant content without echoing it.

### Constraints

- **Tech stack**: React + TypeScript frontend, Python + FastAPI backend, PostgreSQL — proven stack for enterprise web apps
- **Architecture**: Frontend never calls model providers directly — all safety enforcement on backend
- **Safety policy**: Block full content on any policy violation — no redaction or partial display
- **Audit**: Log metadata only — never store raw prompts, raw model outputs, or full PII values
- **Auth**: OIDC integration required — no anonymous access, mock OIDC for MVP
- **Deployment**: Local development first (uvicorn + npm dev + local PostgreSQL) — deployment strategy deferred
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Framework — Frontend
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React | 19.x | UI framework | React 19 stable release (Dec 2024) with improved concurrent rendering, actions, and hooks. Not using RSC since this is a client SPA, but React 19 client-side features are solid. | NEEDS VERIFICATION |
| TypeScript | 5.7.x | Type safety | TypeScript 5.7+ has satisfies operator improvements, better inference. Required for enterprise code quality. | NEEDS VERIFICATION |
| Vite | 6.x | Build tool / dev server | Vite replaces Create React App (deprecated) and webpack. Fast HMR, native ESM, simpler config. The standard for new React projects in 2025. | NEEDS VERIFICATION |
| TanStack Query | 5.x | Data fetching / cache | Formerly React Query. Handles chat API calls, conversation listing, model selection. Caching, retry, stale-while-revalidate built in. Eliminates manual fetch + useEffect patterns. | NEEDS VERIFICATION |
| Zustand | 5.x | Client state management | Minimal, lightweight state for chat session, selected model, auth state. No Redux overhead -- Zustand is 1KB, no boilerplate, TypeScript-first. Perfect for MVP scope. | NEEDS VERIFICATION |
### Core Framework — Backend
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12 | Runtime | Python 3.12 has performance improvements (faster comprehensions, specializing adaptive interpreter). 3.13 is newer but 3.12 is the conservative enterprise choice with broad library support. Avoid 3.11 -- 3.12 perf gains matter for streaming. | MEDIUM |
| FastAPI | 0.115.x | API framework | FastAPI is the standard Python async web framework for APIs. Native Pydantic v2 integration, dependency injection, OpenAPI docs auto-generated, async support for streaming responses. No 1.0 release yet but 0.115+ is stable and production-proven. | NEEDS VERIFICATION |
| uvicorn | 0.34.x | ASGI server | Standard ASGI server for FastAPI. Required for running the app. Use --reload for dev. | NEEDS VERIFICATION |
| Pydantic | 2.x | Data validation / serialization | Comes with FastAPI. Pydantic v2 is a major perf improvement over v1 (5-50x faster). Used for all request/response schemas, SafetyFinding, SafetyDecision, audit event models. | MEDIUM |
| SQLAlchemy | 2.x | ORM / DB access | SQLAlchemy 2.x has native async support (critical for FastAPI), typed queries, modern select() API. Avoid 1.4 legacy patterns. | MEDIUM |
| Alembic | 1.14.x | DB migrations | Standard migration tool for SQLAlchemy. Required for schema evolution as new features add tables. | NEEDS VERIFICATION |
### Database
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PostgreSQL | 16 | Primary database | PostgreSQL 16 (released Sep 2023) is stable and widely deployed. Stores conversations (allowed-through content only), audit events, user profiles, model configs, policy configs. JSONB columns for flexible audit metadata. | MEDIUM |
| asyncpg | 0.30.x | Async PostgreSQL driver | Required for FastAPI async DB access with SQLAlchemy. Do NOT use psycopg2 (sync driver blocks async). | NEEDS VERIFICATION |
### Safety Filtering — DataProtectionScanner (PII, Sensitive Data, Classification)
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Microsoft Presidio (Analyzer) | 2.2.x | PII detection | Industry-standard PII recognizer. 30+ built-in recognizers (PERSON, EMAIL, PHONE, CREDIT_CARD, SSN, IBAN, etc.). Custom recognizers via regex or ML-based. Python-native. MIT license. Wraps behind DataProtectionScanner interface. | NEEDS VERIFICATION |
| Microsoft Presidio (Anonymizer) | 2.2.x | PII anonymization |配套 to analyzer -- replaces detected PII with placeholders. Used internally for audit metadata generation (never echo raw PII). MIT license. | NEEDS VERIFICATION |
| spaCy | 3.7.x | NLP engine for Presidio | Presidio requires an NLP engine for context-aware PII detection. spaCy is the default and best-supported engine for Presidio. Download en_core_web_lg model for accuracy. | NEEDS VERIFICATION |
### Safety Filtering — LLMGuardrailScanner (Jailbreak, Prompt Injection, Harmful Content, Compliance)
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| ProtectAI LLM Guard | 1.2.x | LLM safety scanning | Best choice for MVP. Python library with modular scanners: PromptInjectionScanner, JailbreakScanner, BanSubstringsScanner, BanTopicsScanner, ToxicityScanner, SensitiveDataScanner, RelevanceScanner, SentimentScanner. Each scanner can be enabled/disabled independently. Wraps behind LLMGuardrailScanner interface. Does NOT require running a separate model server. | NEEDS VERIFICATION |
| Alternative | Why Not |
|-------------|---------|
| Meta Llama Guard 3 | Requires running a separate inference model (HuggingFace). Adds infrastructure complexity to MVP. Better as a Phase 2 enhancement behind the same interface. |
| NVIDIA NeMo Guardrails | Conversation-level framework, too heavy for MVP. More suited for chatbot guardrails (controlling what the model says) rather than input/output classification. Steep learning curve. |
| Homegrown keyword/regex filtering | Cannot detect sophisticated prompt injection, jailbreak patterns, or subtle harmful content. Fails at enterprise safety requirements. |
### Authentication (OIDC)
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Authlib | 1.3.x | OIDC client library | Full OIDC/OAuth2 implementation for Python. Handles discovery, token exchange, user info, refresh. Used when real enterprise IDP is connected. | NEEDS VERIFICATION |
| itsdangerous | 2.1.x | Session token signing | For mock OIDC MVP -- sign mock session tokens with TimedSerializer. Lightweight, no server needed. Swapped out when Authlib replaces mock. | MEDIUM |
### Model Provider Integration
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| httpx | 0.28.x | Async HTTP client | Async HTTP client for calling Qwen API and OpenAI-compatible endpoints. Supports streaming responses, timeout configuration, connection pooling. Replaces requests (sync, blocks async loop). | NEEDS VERIFICATION |
| openai Python SDK | 1.x | OpenAI-compatible client | The OpenAI Python SDK supports custom base_url for any OpenAI-compatible endpoint. Use for local LLM calls -- set base_url to local server. Also potentially useful for Qwen if it exposes an OpenAI-compatible API. | MEDIUM |
### Streaming / SSE
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| sse-starlette | 2.x | Server-Sent Events for FastAPI | Adds SSE support to FastAPI/Starlette. Required for streaming chat responses to frontend with safety buffering. StreamingResponse alone doesn't handle SSE framing. | NEEDS VERIFICATION |
| eventsource-parser | 2.x | SSE client parser (frontend) | Parse SSE stream on frontend. Standard for consuming streaming API responses in browser. | NEEDS VERIFICATION |
### Infrastructure / Dev Tooling
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| ruff | 0.11.x | Linter + formatter | Replaces flake8, isort, black. Single tool for linting and formatting. Extremely fast (Rust-based). Already specified in SPEC.md. | NEEDS VERIFICATION |
| pytest | 8.x | Test framework | Standard Python test framework. pytest-asyncio for async test support (required for FastAPI). | NEEDS VERIFICATION |
| pytest-asyncio | 0.24.x | Async test support | Required for testing async FastAPI endpoints and streaming. | NEEDS VERIFICATION |
| httpx (test) | 0.28.x | Test HTTP client | httpx.AsyncClient used as test client for FastAPI (replaces TestClient for async routes). | MEDIUM |
| Vitest | 3.x | Frontend test framework | Vite-native test runner. Faster than Jest for Vite projects. TypeScript and React support built in. | NEEDS VERIFICATION |
| React Testing Library | 16.x | Component testing | Standard for testing React components by simulating user behavior. Tests chat display, blocked-message rendering, model selection. | NEEDS VERIFICATION |
### Supporting Libraries — Backend
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| python-dotenv | 1.x | Load .env files | Load DB connection strings, model API keys, OIDC config from .env. Development-only convenience. | MEDIUM |
| structlog | 24.x | Structured logging | Replace print/logging with structured JSON logs. Audit events get proper logging. Custom processors for filtering sensitive data from logs. | NEEDS VERIFICATION |
| tenacity | 9.x | Retry logic | Retry model provider calls with exponential backoff. Handles transient network failures. | NEEDS VERIFICATION |
### Supporting Libraries — Frontend
| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| Tailwind CSS | 4.x | Utility CSS | Rapid UI development without writing custom CSS. Standard for React apps in 2025. Use for chat UI, admin dashboard, blocked message styling. | NEEDS VERIFICATION |
| React Router | 7.x | Client routing | SPA routing for /chat, /admin, /auth pages. React Router 7 is the current major version (remix merged back). | NEEDS VERIFICATION |
| Lucide React | 0.4xx | Icon library | Lightweight SVG icons for UI elements. Smaller bundle than Font Awesome or Material Icons. | NEEDS VERIFICATION |
## Alternatives Considered
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Frontend framework | React 19 | Vue 3 / Angular | Project spec mandates React. Vue is fine but not chosen. Angular is overkill for MVP scope. |
| Frontend build | Vite 6 | webpack / CRA | Create React App is deprecated. webpack is slower and more complex. Vite is the 2025 standard. |
| Backend framework | FastAPI | Django / Flask | Django is too heavy (ORM, admin, templates) for an API-only service. Flask lacks native async -- streaming requires async. FastAPI is the right tool. |
| ORM | SQLAlchemy 2 | Django ORM / Tortoise ORM | Django ORM tied to Django framework. Tortoise ORM is async but less mature, smaller ecosystem, weaker migration tooling. SQLAlchemy 2 async is proven. |
| State management | Zustand | Redux Toolkit / Jotai | Redux adds boilerplate (actions, reducers, selectors) disproportionate to MVP scope. Jotai is fine but Zustand has better docs and simpler API for this scope. |
| PII detection | Presidio | Homegrown regex / AWS Comprehend | Regex misses contextual PII (name near phone number). Comprehend is cloud-only, costs money, adds latency. Presidio is local, Python-native, extensible. |
| LLM guardrails | LLM Guard | Llama Guard 3 / NeMo Guardrails | Llama Guard 3 needs separate model server (infrastructure burden for MVP). NeMo Guardrails is a conversation framework (wrong abstraction level). LLM Guard is a Python library, modular, covers all MVP scanner categories. |
| HTTP client | httpx | requests / aiohttp | requests is sync (blocks async loop). aiohttp is async but httpx is simpler, FastAPI ecosystem standard, supports both sync and async. |
| CSS | Tailwind CSS | CSS Modules / styled-components | CSS Modules require writing more CSS. styled-components adds runtime overhead. Tailwind is fastest for MVP prototyping. |
| Icons | Lucide React | Font Awesome / Material Icons | Font Awesome has licensing concerns for enterprise (commercial use). Material Icons heavier bundle. Lucide is MIT, lightweight, tree-shakeable. |
## What NOT to Use and Why
| Technology | Why Avoid | What to Use Instead |
|------------|-----------|---------------------|
| Create React App | Deprecated and unmaintained since 2023. Webpack-based, slow HMR. | Vite |
| Redux | Excessive boilerplate for MVP. Actions, reducers, selectors, middleware for 3 pieces of state. | Zustand |
| requests library | Synchronous HTTP client. Calling model APIs with requests blocks the async event loop, breaks streaming. | httpx (async) |
| psycopg2 | Synchronous PostgreSQL driver. Same blocking problem as requests. | asyncpg |
| Flask | No native async support. Streaming chat with safety buffering requires async throughout. | FastAPI |
| Homegrown regex/keyword filtering for safety | Cannot detect prompt injection patterns, jailbreak obfuscation, or subtle harmful content. Enterprise safety requires ML-based detection. | Presidio + LLM Guard |
| Jest | Slower than Vitest for Vite projects. Requires babel/swc transform config. | Vitest |
| Global mutable state on backend | Thread-safety issues in async context, hard to reason about, audit trail breaks. | Request-scoped dependency injection (FastAPI Depends) |
| Echoing blocked content in error messages | Violates project core requirement: block messages must NOT echo sensitive content. | Fixed safe explanation messages by risk category |
## Installation
# === Backend ===
# Core
# Database
# Safety filtering
# Model providers
# Auth
# Streaming
# Infrastructure
# === Frontend ===
# Core
# Routing
# Styling
# Streaming
# Dev / Test
## Version Verification Checklist
# Backend versions (run in venv)
# Frontend versions
## Sources
- Project SPEC.md and PROJECT.md (primary context for tech choices)
- .planning/notes/key-decisions.md (confirmed: Presidio + LLM Guard, mock OIDC, local dev first)
- .planning/todos/pending/filter-library-selection.md (detailed filter library candidates)
- Training data for version numbers (ALL marked NEEDS VERIFICATION -- could not access web due to tool restrictions)
- Confidence assessment based on ecosystem maturity and project specification alignment
## Confidence Assessment
| Area | Confidence | Reason |
|------|------------|--------|
| Core frameworks (React, FastAPI, PostgreSQL) | MEDIUM | Project spec mandates these. Version numbers from training data need verification. Choices are standard and well-justified. |
| Safety filtering (Presidio, LLM Guard) | MEDIUM | Presidio is clearly the best PII choice. LLM Guard is best for MVP guardrails but version needs verification. Llama Guard deferred to Phase 2. |
| Auth (Authlib, mock OIDC) | MEDIUM | Mock OIDC strategy is clear from project decisions. Authlib is the standard OIDC library but version needs verification. |
| Streaming (SSE, eventsource-parser) | LOW | Streaming with safety buffering is architecturally complex. Library choices are reasonable but need deeper research on buffering patterns. |
| Frontend tooling (Vite, Vitest, TanStack Query) | MEDIUM | Standard 2025 choices. Version numbers need verification but library selections are well-justified. |
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
