# Enterprise AI Chat MVP — Feature & Tech Stack Specification

## Functional Overview

Enterprise AI Chat MVP is a safety-first web application that lets authenticated employees chat with approved LLMs while enforcing strict input and output safety controls. The system blocks sensitive content before model calls and blocks unsafe model responses before display — never echoing the blocked content back to the user.

### Core Features

| Feature | Description | Implementation |
|---------|-------------|---------------|
| **Authentication** | Mock OIDC login with role selector (employee/admin). Session-based auth with signed cookies. | `backend/app/auth/` — MockOIDCProvider, session tokens, role-based access control |
| **Chat** | Employees select a model and send messages. Responses go through the safety pipeline before display. | `backend/app/api/chat.py` — POST /send with input scan → model → output scan |
| **Streaming Chat** | SSE-based streaming with sentence-buffered safety scanning. Text appears incrementally; unsafe sentences trigger full block. | `backend/app/api/chat_stream.py` + `streaming/service.py` + `buffer.py` |
| **Safety Pipeline** | Multi-scanner parallel scan with 30s timeout and fail-closed semantics. Any scanner crash/timeout → block. | `backend/app/safety/pipeline.py` — asyncio.gather with timeout, SafetyPolicy aggregation |
| **PII Detection** | Detects personal/sensitive information (email, phone, SSN, credit card, Chinese national ID, etc.) with regex-based recognizers. | `backend/app/safety/data_protection.py` — Presidio AnalyzerEngine with custom recognizers, score threshold 0.7 |
| **Content Guard** | Three-layer detection: regex injection patterns, regex harmful content patterns, Qwen3Guard-Gen-0.6B generative model. Covers Chinese + English. | `backend/app/safety/llm_guardrails.py` — ContentGuardScanner |
| **Block Messages** | Category-specific Chinese block templates. Never echoes raw detected content. Includes revision hints. | `backend/app/safety/block_messages.py` — 6 risk categories × input/output templates |
| **Conversation History** | Browse past conversations, resume conversations, continue chatting. Only allowed-through content stored. | `backend/app/conversations/repository.py` — CRUD for conversations and messages |
| **Admin Dashboard** | View audit events with filters/stats, manage model configs (CRUD + encrypted keys), manage scanner policies. | `backend/app/api/admin.py` + `frontend/src/features/admin/` |
| **DB-First Model Config** | Model configs stored in DB with Fernet-encrypted API keys. Admin changes take effect immediately. Env vars only seed initial configs. | `backend/app/models/providers.py` — ProviderRegistry reads from ModelConfig table |
| **Auto-Degrade** | If SSE streaming fails (5xx, connection drop, timeout), frontend falls back to non-streaming /send endpoint. | `frontend/src/features/chat/useStreamChat.ts` — fallback to sendChatMessage |
| **Audit Trail** | Records metadata-only audit events for every safety decision. Never stores raw prompts or outputs. | `backend/app/audit/repository.py` — AuditRepository with user_id, model_id, categories, action |

### Safety Pipeline Detail

The safety pipeline is the system's core value. It runs **before every model call** (input scan) and **after every model response** (output scan).

**Scanner Architecture:**

| Scanner | Detection Method | Coverage | Risk Categories |
|---------|-----------------|----------|----------------|
| DataProtectionScanner | Presidio regex recognizers (EMAIL, PHONE, SSN, CREDIT_CARD, IBAN, IP_ADDRESS, Chinese National ID) + custom recognizers (Employee ID, Project Code, Income) | High-confidence regex matches only; NLP-dependent entities removed to avoid Chinese false positives | pii, sensitive_data |
| ContentGuardScanner — Regex Injection Rules | 30+ regex patterns covering English and Chinese instruction override, identity manipulation, safety bypass, system access | Deterministic, zero false positives on normal text | prompt_injection, jailbreak |
| ContentGuardScanner — Regex Harmful Content Rules | 12+ regex patterns covering English and Chinese hate speech, discrimination, racist jokes requests | Deterministic, zero false positives on normal queries | harmful_content |
| ContentGuardScanner — Qwen3Guard-Gen-0.6B | Generative guard model producing structured safe/unsafe + category output | Probabilistic, covers content rules don't reach. Works well on Chinese and English | harmful_content, compliance, pii, jailbreak |

**Policy Decision Flow:**

```
All scanners run in parallel (asyncio.gather, 30s timeout)
  → If any scanner crashes/timeout → None result (not a violation, not an allow)
  → If ALL scanners crash → fail_closed (block with system error message)
  → SafetyPolicy aggregates valid findings:
    → No violations → allow (proceed to model call or display)
    → Any violation → block (full content block, category-specific Chinese message)
    → Uses highest-severity category for block message template
```

**Fail-Closed Guarantees:**

- Scanner timeout → fail_closed (block, not allow)
- Scanner crash → None result, but if all scanners fail → fail_closed
- No partial display: if ANY sentence in streaming output has a violation, ENTIRE output is blocked
- Block messages never echo detected content

### Risk Categories & Block Messages

| Category | Input Block Message | Output Block Message |
|----------|--------------------|--------------------|
| pii (个人信息) | 您的消息因包含个人或敏感信息而被拦截。请移除个人敏感信息后重试。 | 回复因包含个人或敏感信息而被拦截。请尝试其他问题。 |
| sensitive_data (敏感数据) | 您的消息因包含企业敏感数据而被拦截。请移除敏感标识后重试。 | 回复因包含企业敏感数据而被拦截。请尝试其他问题。 |
| prompt_injection (指令注入) | 您的消息因疑似包含指令注入而被拦截。请用自然语言重新表述。 | 回复因疑似包含操控指令而被拦截。请尝试其他问题。 |
| jailbreak (越狱) | 您的消息因疑似绕过安全约束而被拦截。请重新表述您的消息。 | 回复因包含越狱内容而被拦截。请尝试其他问题。 |
| harmful_content (有害内容) | 您的消息因包含有害或不当内容而被拦截。请移除不当内容后重试。 | 回复因包含有害或不当内容而被拦截。请尝试其他问题。 |
| compliance (合规) | 您的消息因可能违反合规政策而被拦截。请参考组织合规指南。 | 回复因可能违反合规政策而被拦截。请尝试其他问题。 |

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.13 | Runtime — async support, type hints |
| FastAPI | 0.115+ | Async API framework with Pydantic v2, dependency injection, OpenAPI docs |
| Uvicorn | 0.34+ | ASGI server for FastAPI |
| SQLAlchemy | 2.x | ORM with native async support (select() API) |
| aiosqlite | — | Async SQLite driver (WAL mode + busy_timeout for concurrent access) |
| Pydantic | 2.x | Request/response validation, 5-50x faster than v1 |
| Microsoft Presidio | 2.2+ | PII detection (AnalyzerEngine) with custom recognizers |
| spaCy | 3.7+ | NLP engine for Presidio (en_core_web_lg model) |
| Transformers + torch | — | Qwen3Guard-Gen-0.6B generative guard model (AutoModelForCausalLM) |
| cryptography (Fernet) | — | API key encryption/decryption in ModelConfig table |
| httpx | 0.28+ | Async HTTP client for Qwen DashScope API |
| openai SDK | 1.x | OpenAI-compatible client for local LLM endpoints |
| tenacity | 9+ | Retry logic for model provider calls (exponential backoff) |
| sse-starlette | 2+ | Server-Sent Events support for FastAPI |
| python-dotenv | 1+ | Load APIKEY.env and .env configuration |
| itsdangerous | 2+ | Session token signing (TimedSerializer for mock OIDC) |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI framework with concurrent rendering |
| TypeScript | 5.7+ | Type safety |
| Vite | 6.x | Build tool / dev server with HMR |
| TanStack Query | 5.x | Data fetching, caching, invalidation (chat models, conversations, admin data) |
| Zustand | 5.x | Client state (selectedModel, activeConversation, messages, auth) |
| Tailwind CSS | 4.x | Utility CSS with @tailwindcss/vite plugin |
| React Router | 7.x | SPA routing (/chat, /admin, /auth) |
| Lucide React | 0.4xx | SVG icons |
| eventsource-parser | 2+ | SSE stream parsing on frontend |
| Vitest | 3.x | Frontend test runner |
| React Testing Library | 16+ | Component testing |

### Database

| Technology | Purpose |
|------------|---------|
| SQLite (WAL mode) | MVP development database. WAL allows concurrent reads during writes, busy_timeout=30s for write contention |
| PostgreSQL | Production target — switch via DATABASE_URL env var, asyncpg driver |

### Model Providers

| Provider | Endpoint | Config |
|----------|----------|--------|
| Qwen (Alibaba DashScope) | https://dashscope.aliyuncs.com/compatible-mode/v1 | OpenAI-compatible API, model_id from admin DB config (e.g. qwen-plus) |
| OpenAI-compatible (local) | Configurable (Ollama, vLLM, etc.) | base_url from admin DB config, api_key configurable (default: "ollama") |

## Project Structure

### Backend

```
backend/
  app/
    main.py              — FastAPI entry point, router registration, logging config
    api/
      auth.py            — Mock OIDC login + callback + /me
      chat.py            — POST /send + GET /models (non-streaming)
      chat_stream.py     — POST /stream (SSE)
      conversations.py  — GET conversations + messages
      admin.py           — Admin CRUD endpoints (models, policy, audit)
    auth/
      current_user.py    — get_current_user / get_admin_user dependencies
      oidc.py            — MockOIDCProvider
    safety/
      pipeline.py        — SafetyPipeline (parallel scan + timeout)
      scanner_interface.py — Scanner protocol + RiskCategory + PolicyDecision types
      data_protection.py — DataProtectionScanner (Presidio + custom recognizers)
      llm_guardrails.py  — ContentGuardScanner (regex + Qwen3Guard model)
      policy.py          — SafetyPolicy (aggregation → allow/block/fail_closed)
      block_messages.py  — Chinese block message templates
      custom_recognizers.py — ChineseNationalId, EmployeeId, ProjectCode, Income
      torch_compat.py    — torch.jit.script no-op patch
    models/
      providers.py       — ProviderRegistry (DB-first) + ModelProvider ABC
      qwen.py            — QwenProvider (httpx async client)
      openai_compatible.py — OpenAICompatibleProvider (openai SDK)
    streaming/
      service.py         — StreamingChatService (orchestrate buffer + scan + SSE)
      buffer.py          — SentenceBuffer (regex sentence splitting)
    conversations/
      repository.py      — Conversation + Message CRUD
    audit/
      repository.py      — AuditEvent recording
      events.py          — AuditEventResponse model
      queries.py         — Paginated queries + stats
    admin/
      models_repo.py     — ModelConfig CRUD + encrypt/decrypt/mask API keys
      policy_repo.py     — PolicyConfig CRUD + auto-seed defaults
    db/
      __init__.py        — Engine, session factory, init_db, SQLite pragmas
      schema.py          — SQLAlchemy models (User, Session, Conversation, Message, AuditEvent, ModelConfig, PolicyConfig)
      seed_data.py       — Seed mock users + model configs from env vars
```

### Frontend

```
frontend/src/
  features/
    auth/           — LoginPage, MockOIDCPage, AuthCallbackPage
    chat/           — ChatPage, ModelSelector, ChatMessages, ChatInput,
                      ConversationSidebar, StreamingMessage, useStreamChat hook
    admin/          — AdminLayout, AdminSidebar, AuditPage, ModelsPage, PolicyPage
                      + components (ModelCard, ModelEditModal, ScannerRow, ConfirmDialog, Toast, etc.)
  stores/
    chatStore.ts    — Zustand: selectedModel, messages, activeConversationId
    authStore.ts    — Zustand: user, isAuthenticated, role
  lib/
    api.ts          — apiClient (fetch wrapper with auth + 204 handling), query functions
```

## Security Design

| Threat | Mitigation |
|--------|-----------|
| Prompt injection / jailbreak | ContentGuardScanner regex rules + Qwen3Guard model |
| PII leakage in user input | DataProtectionScanner blocks before model call |
| Unsafe model output | Output scan blocks before display; streaming uses sentence buffer |
| Content echo in block messages | Templates use category labels only, never raw detected text |
| Scanner crash/timeout | Fail-closed: block content rather than allow unfiltered |
| API key exposure | Fernet encryption in DB; admin UI shows masked keys only (last 4 chars) |
| Unauthorized admin access | get_admin_user dependency checks role == "admin", returns generic 403 |
| Session hijacking | Signed session tokens (itsdangerous), httponly cookies |