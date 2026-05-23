<!-- generated-by: gsd-doc-writer -->

# Enterprise AI Chat MVP

An enterprise AI chat web application that lets authenticated employees chat with approved LLMs while enforcing input and output safety controls. The MVP proves that AI chat can be used safely in a controlled enterprise environment -- blocking sensitive content before model calls and blocking unsafe model responses before display.

## Installation

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### Frontend

```bash
cd frontend
npm install
```

## Quick Start

1. Set up API keys in `APIKEY.env` (project root):
   ```
   QWEN_API_KEY=your-dashscope-api-key
   SECRET_KEY=dev-secret-change-this
   ```
2. Start the backend:
   ```bash
   cd backend
   .venv\Scripts\Activate.ps1   # or source .venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```
3. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```
4. Open the app and log in with mock OIDC (employee or admin role).

## Usage Examples

### Chat with safety enforcement

Send a message through the chat interface. The backend runs a three-stage safety pipeline:

- **Input scan** -- DataProtectionScanner (Presidio PII detection + custom recognizers for Chinese national ID, employee ID, project codes) and ContentGuardScanner (regex-based injection/harmful content rules + Qwen3Guard-Gen-0.6B generative guard model) scan the user message. If any violation is found, the message is blocked with a category-specific explanation -- the sensitive content is never echoed.
- **Model call** -- The clean message is sent to the configured LLM (Alibaba Qwen via DashScope API, or a local OpenAI-compatible endpoint).
- **Output scan** -- The model response is buffered sentence-by-sentence and scanned through the same safety pipeline. If any sentence triggers a violation, the entire output is blocked per project policy (no redaction, no partial display).

### Streaming chat (SSE)

The `POST /api/chat/stream` endpoint returns Server-Sent Events. The frontend consumes the stream with `eventsource-parser`, displaying chunks as they arrive. If a safety violation is detected in the output, a `blocked` event replaces all streamed content.

### Admin dashboard

Admin users can access `/admin/audit` for audit log browsing, `/admin/models` for model configuration (add/remove LLM providers, manage encrypted API keys), and `/admin/policy` for scanner policy configuration (enable/disable scanners, set sensitivity levels).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, TanStack Query, Zustand, Tailwind CSS, React Router |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy 2 (async), Alembic |
| Database | SQLite via aiosqlite (MVP); PostgreSQL via asyncpg for production |
| Safety | Microsoft Presidio (PII), spaCy NLP, regex rules + Qwen3Guard-Gen-0.6B (content guard) |
| Auth | Mock OIDC (itsdangerous token signing); real OIDC via Authlib for production |
| Streaming | sse-starlette (backend SSE), eventsource-parser (frontend) |
| HTTP | httpx (async client for model provider calls) |
| Testing | pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend) |
| Linting | ruff (backend), ESLint (frontend) |

## Project Structure

```
ai_chat_tool/
  backend/
    app/
      api/          # FastAPI route handlers (auth, chat, chat_stream, conversations, admin)
      auth/         # Mock OIDC provider + current user dependency
      admin/        # Admin repository queries (audit, model config, policy config)
      audit/        # Audit event repository
      conversations/ # Conversation and message CRUD
      db/           # SQLAlchemy schema, session factory, migrations
      models/       # Model provider interface, registry, Qwen/OpenAI adapters
      safety/       # Scanner interface, pipeline, DataProtectionScanner, ContentGuardScanner, policy, block messages
      streaming/    # SentenceBuffer + StreamingChatService (SSE orchestration)
      tests/        # pytest integration tests
    requirements.txt
  frontend/
    src/
      features/
        auth/       # LoginPage, MockOIDCPage, AuthCallbackPage
        chat/       # ChatPage, ChatInput, ChatMessages, StreamingMessage, BlockedMessage, ModelSelector, ConversationSidebar
        admin/      # AdminLayout, AuditPage, ModelsPage, PolicyPage, UI components
      stores/       # Zustand stores (authStore, chatStore)
      lib/          # api.ts (HTTP client + SSE, TanStack Query config)
      routes.tsx    # React Router config with ProtectedRoute/AdminRoute guards
    package.json
```

<!-- VERIFY: Deployment strategy is deferred per project spec -->