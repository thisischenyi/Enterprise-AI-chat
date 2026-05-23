<!-- generated-by: gsd-doc-writer -->

# Development Guide

This guide covers how to develop, run, test, and extend the Enterprise AI Chat MVP. It is written for developers joining the project who need to understand the codebase conventions, patterns, and workflow.

## Running Backend + Frontend Together

The project runs as two separate processes in local development. The frontend Vite dev server proxies API requests to the backend, so no CORS configuration is needed.

### Backend

```bash
cd backend

# Create and activate virtual environment (first time only)
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (required for Presidio PII detection)
python -m spacy download en_core_web_lg

# Start the server
uvicorn app.main:app --reload --port 8000
```

The backend starts on `http://localhost:8000`. The `--reload` flag watches for file changes and restarts automatically. The startup lifespan handler (`app/main.py`) creates database tables and seeds two mock users.

### Frontend

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

The frontend starts on `http://localhost:5173` (Vite default). All `/api` requests are proxied to `http://localhost:8000` via the proxy configuration in `frontend/vite.config.ts`.

### First-Time Login

The backend seeds two mock users on startup. Use the mock OIDC login flow:

1. Navigate to `http://localhost:5173/login`
2. Select role (employee or admin)
3. Complete the mock OIDC callback flow

The mock OIDC provider (`backend/app/auth/oidc.py`) uses itsdangerous TimedSerializer for state and session token signing. Session cookies are set with `httponly=True` and `samesite="lax"` for local development.

### Environment Variables

Backend variables are loaded from `APIKEY.env` in the project root (loaded in `backend/app/main.py`) and `backend/.env` via python-dotenv (loaded in `backend/app/db/__init__.py`). See `docs/CONFIGURATION.md` for the full variable reference.

At minimum, you need one model provider credential to make chat work:
- `QWEN_API_KEY` or `DASHSCOPE_API_KEY` for Qwen models
- `OPENAI_API_BASE` or `LOCAL_LLM_BASE_URL` for local OpenAI-compatible models

The frontend reads `VITE_API_BASE_URL` from `frontend/.env` (defaults to `/api`).

## Code Style and Conventions

### Backend (Python / ruff)

The backend uses **ruff** for linting and formatting. It is installed as a project dependency (listed in `requirements.txt`). No separate `ruff.toml` or `pyproject.toml` configuration file exists in the backend directory -- ruff runs with its default settings.

```bash
cd backend
# Lint all source files
ruff check app/

# Format all source files
ruff format app/
```

Key style conventions observed in the codebase:
- **Type hints everywhere** -- all function signatures include parameter and return types. Use `from __future__ import annotations` for forward references.
- **Dataclasses over dict returns** -- scanner results (`ScannerResult`, `ScannerFinding`, `PolicyDecision`) use dataclasses with typed fields.
- **Pydantic models for API schemas** -- request/response models in route files use Pydantic `BaseModel` with `Field` validators.
- **SQLAlchemy 2 style** -- models use `Mapped[]` type annotations and `mapped_column()` (not legacy `Column()`).
- **Docstrings on all public modules** -- every module file starts with a triple-quote docstring explaining its purpose.
- **async/await throughout** -- no sync database calls or HTTP calls. Presidio and transformers calls use `asyncio.to_thread()` for async compatibility.
- **Chinese block messages** -- user-facing block messages are in Chinese (`block_messages.py`). Internal logging and code comments are in English.

<!-- VERIFY: Whether ruff has any custom rule overrides or line-length settings beyond defaults -->

### Frontend (TypeScript / ESLint)

The frontend uses **ESLint** with the flat config format (`eslint.config.js`). Configuration includes:
- `@eslint/js` recommended rules
- `typescript-eslint` recommended rules
- `eslint-plugin-react-hooks` recommended (enforces rules of hooks)
- `eslint-plugin-react-refresh` Vite plugin

```bash
cd frontend
# Lint
npm run lint

# Build (also type-checks)
npm run build
```

Key style conventions observed in the codebase:
- **Feature-slice organization** -- components live in `src/features/{feature}/` directories, not scattered across generic folders.
- **Zustand for state** -- minimal stores in `src/stores/` with `create()` API. No Redux patterns.
- **TanStack Query for data fetching** -- all server state uses `useQuery` / `queryClient.invalidateQueries`. No manual fetch+useEffect patterns.
- **Named exports** -- components use `export default function ComponentName()` (one component per file).
- **Tailwind CSS** -- all styling uses utility classes. No custom CSS files except `index.css` for base styles.

## Project Structure Overview

### Backend Modules

```
backend/app/
  main.py              # FastAPI app entry point, lifespan handler, router registration
  api/                 # Route handlers — thin layer, business logic lives in domain modules
    auth.py            # POST /api/auth/login, /callback, GET /me
    chat.py            # POST /api/chat/send, GET /api/chat/models (non-streaming)
    chat_stream.py     # POST /api/chat/stream (SSE streaming)
    conversations.py   # GET /api/conversations, /{id}/messages
    admin.py           # GET/POST/PUT/DELETE /api/admin/models, /policy, GET /audit
  auth/                # Authentication
    oidc.py            # OIDCProvider ABC + MockOIDCProvider (itsdangerous signing)
    current_user.py    # FastAPI Depends: get_current_user, get_admin_user (session cookie -> DB lookup)
  safety/              # Safety pipeline and scanners — the core enforcement module
    scanner_interface.py  # Scanner protocol, ScannerResult, ScannerFinding, PolicyDecision, RiskCategory
    pipeline.py        # SafetyPipeline — parallel scanner execution with 30s fail-closed timeout
    policy.py          # SafetyPolicy — evaluate findings into allow/block/fail_closed decisions
    data_protection.py # DataProtectionScanner — Presidio PII/sensitive data detection
    llm_guardrails.py  # ContentGuardScanner — regex injection rules + harmful content rules + Qwen3Guard model
    custom_recognizers.py # Custom Presidio recognizers (ChineseNationalId, EmployeeId, ProjectCode, Income)
    block_messages.py  # Category-specific block message templates (Chinese, never echo content)
    torch_compat.py    # torch.jit.script no-op patch (must import before transformers)
  models/              # Model provider integrations
    providers.py       # ModelProvider ABC, ProviderRegistry, get_provider_registry dependency
    qwen.py            # QwenProvider — Alibaba DashScope via httpx with tenacity retry
    openai_compatible.py # OpenAICompatibleProvider — generic endpoint via AsyncOpenAI SDK
  streaming/           # SSE streaming infrastructure
    buffer.py          # SentenceBuffer — sentence-boundary token splitting
    service.py         # StreamingChatService — orchestrates buffer + scan + SSE event generation
  conversations/       # Conversation and message persistence
    repository.py      # ConversationRepository — CRUD with user ownership filtering
  audit/               # Audit event recording
    events.py          # AuditEventResponse Pydantic model
    repository.py      # AuditRepository — metadata-only event recording
  admin/               # Admin data access (separate from API routing)
    audit_queries.py   # Paginated audit event queries with multi-dimension filters
    models_repo.py     # ModelConfig CRUD with Fernet-encrypted API key storage
    policy_repo.py     # PolicyConfig CRUD for scanner enable/sensitivity settings
  db/                  # Database configuration and schema
    __init__.py        # Async SQLAlchemy engine (SQLite/aiosqlite), session factory, init_db
    schema.py          # SQLAlchemy models: User, Session, Conversation, Message, AuditEvent, ModelConfig, PolicyConfig
    seed_data.py       # Mock user seeding on startup (employee + admin)
    migrations/        # Alembic migration infrastructure
  tests/               # Backend test suite
    conftest.py        # Shared test fixtures: in-memory SQLite, mock user seeding, async client
    test_auth.py       # Auth endpoint tests
    test_safety_pipeline.py # Safety pipeline integration tests (allow, block, fail-closed paths)
    test_chat_api.py   # Chat endpoint tests with mock pipeline and mock provider
    test_role_access.py # Role-based access tests (admin-only endpoints)
    test_fixtures.py   # Mock scanner implementations for tests
```

### Frontend Feature Slices

```
frontend/src/
  main.tsx             # Vite entry point
  App.tsx              # Root component (Providers + AppRoutes)
  routes.tsx           # React Router config with ProtectedRoute and AdminRoute guards
  app/
    providers.tsx      # QueryClientProvider + AuthRestorer (cookie session recovery on mount)
  features/
    auth/              # Login, mock OIDC page, auth callback, user info display
      LoginPage.tsx
      MockOIDCPage.tsx
      AuthCallbackPage.tsx
      UserInfo.tsx
    chat/              # Core chat UI
      ChatPage.tsx     # Main chat page (orchestrates sidebar, messages, input, streaming)
      ChatMessages.tsx # Message list rendering
      ChatInput.tsx    # Input bar with send button
      StreamingMessage.tsx # Live streaming message display (text + redacted segments)
      BlockedMessage.tsx   # Block message display with risk category badges
      ConversationSidebar.tsx # Conversation history sidebar
      ModelSelector.tsx # Model dropdown selector
      useStreamChat.ts # SSE streaming hook with auto-degrade to non-streaming fallback
    admin/             # Admin dashboard
      AdminLayout.tsx  # Layout wrapper with sidebar navigation
      AdminSidebar.tsx # Admin section navigation
      AuditPage.tsx    # Audit event viewer with filters
      ModelsPage.tsx   # Model configuration CRUD
      PolicyPage.tsx   # Scanner policy configuration
      components/      # Shared admin UI components
        ActionBadge.tsx, AuditFilters.tsx, AuditStatCards.tsx, AuditTable.tsx
        Pagination.tsx, SparklineChart.tsx, ConfirmDialog.tsx, ModelCard.tsx
        ModelEditModal.tsx, ScannerRow.tsx, Toast.tsx
  stores/              # Zustand global state
    authStore.ts       # Auth state: user, login, callback, fetchUser, logout
    chatStore.ts       # Chat state: selectedModel, messages, loading, activeConversationId
  lib/                 # Shared utilities
    api.ts             # apiClient fetch wrapper, TanStack QueryClient, API type definitions
  tests/               # Frontend test suite
    auth.test.tsx      # Auth flow tests
    roleAccess.test.tsx # Role-based route access tests
    setup.ts           # Vitest setup
```

## Making Changes

### Adding a New API Endpoint

1. Create or add to a route file in `backend/app/api/`. Each file defines an `APIRouter()` and exports it.
2. Add the router to `backend/app/main.py` with a prefix:
   ```python
   app.include_router(new_module.router, prefix="/api/new-module", tags=["new-module"])
   ```
3. Use `Depends(get_current_user)` for authenticated endpoints, `Depends(get_admin_user)` for admin-only endpoints.
4. Use `Depends(get_db_session)` for endpoints that need database access. The dependency auto-commits on success and auto-rollbacks on exception.
5. Define request/response Pydantic models in the same route file (the codebase keeps them close to their handlers, not in a separate schemas module).

Example pattern from `backend/app/api/conversations.py`:
```python
@router.get("")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ConversationSummary]:
    repo = ConversationRepository(db)
    ...
```

### Adding a New Frontend Feature

1. Create a new directory under `frontend/src/features/{feature-name}/`.
2. Add components following the naming convention: `PascalCase.tsx` for components.
3. If the feature needs global state, add a slice to a Zustand store in `frontend/src/stores/` or create a new store.
4. If the feature fetches server data, use TanStack Query (`useQuery` for reads, mutations for writes) via `frontend/src/lib/api.ts`.
5. Add routes in `frontend/src/routes.tsx` wrapped in `ProtectedRoute` or `AdminRoute` as appropriate.

### Adding a New Safety Scanner

1. Implement the `Scanner` protocol defined in `backend/app/safety/scanner_interface.py`:
   ```python
   class MyNewScanner:
       async def scan(self, content: str, source: Literal["input", "output"]) -> ScannerResult:
           findings = [...]
           return ScannerResult(findings=findings, has_violations=len(findings) > 0, scanner_name="my_new_scanner")
   ```
2. Add your scanner class in a new file under `backend/app/safety/`.
3. Register it in the `get_safety_pipeline()` dependency in `backend/app/api/chat.py` -- add an import and `scanners.append(MyNewScanner())` in the try/except block.
4. Add a `RiskCategory` enum value in `backend/app/safety/scanner_interface.py` if your scanner detects a new risk type.
5. Add a block message template for the new category in `backend/app/safety/block_messages.py` -- both `"input"` and `"output"` variants.
6. Map your category to the severity ordering in `block_messages.py` (`_SEVERITY_ORDER`).
7. If using Presidio, add custom recognizers in `backend/app/safety/custom_recognizers.py` and register them in `DataProtectionScanner.__init__()`.

**Important**: The safety pipeline runs all scanners in parallel via `asyncio.gather`. CPU-bound scanner work (regex matching, model inference) must use `asyncio.to_thread()` to avoid blocking the async event loop. See `DataProtectionScanner.scan()` and `ContentGuardScanner.scan()` for examples.

### Adding a New Model Provider

1. Subclass `ModelProvider` ABC from `backend/app/models/providers.py`:
   ```python
   class MyProvider(ModelProvider):
       provider_id: str = "my-provider"
       model_id: str  # set in __init__
       display_name: str = "My Provider"
       description: str = "Description"
       async def chat_completion(self, messages: list[dict[str, str]]) -> str:
           ...
   ```
2. Add the provider file in `backend/app/models/`.
3. Add environment variable handling in `ProviderRegistry._init_providers()` in `providers.py`.

### Adding a New Database Table

1. Define the SQLAlchemy model in `backend/app/db/schema.py` using the `Mapped[]` / `mapped_column()` style.
2. Create an Alembic migration in `backend/app/db/migrations/versions/`.
3. Add a repository class in the appropriate domain module (e.g., `backend/app/conversations/repository.py` pattern).

## Key Patterns

### Dependency Injection (FastAPI Depends)

The backend uses FastAPI's `Depends()` for all cross-cutting concerns. The key dependencies:

| Dependency | File | Purpose |
|---|---|---|
| `get_current_user` | `app/auth/current_user.py` | Extracts user from session cookie via DB lookup; 401 if invalid/expired |
| `get_admin_user` | `app/auth/current_user.py` | Chains `get_current_user` + checks `role == "admin"`; 403 if not admin |
| `get_db_session` | `app/db/__init__.py` | Yields `AsyncSession`, auto-commits on success, auto-rollbacks on exception |
| `get_safety_pipeline` | `app/api/chat.py` | Creates `SafetyPipeline` with real scanners, graceful fallback if deps unavailable |
| `get_provider_registry` | `app/models/providers.py` | Creates `ProviderRegistry` from environment credentials |

For SSE streaming endpoints (`chat_stream.py`), the DB session is managed manually inside `_event_generator()` rather than via `Depends()` -- SSE responses hold sessions for the entire connection duration, which would block the SQLite write lock if using the standard dependency. The generator uses `asyncio.shield()` on cleanup to prevent session leaks when the client disconnects.

### Safety Pipeline

The safety pipeline follows a **fail-closed** design: any scanner failure (timeout, crash, or detection) results in blocking the content. The flow:

1. `SafetyPipeline.scan_input()` / `scan_output()` receives content and runs all registered scanners in parallel via `asyncio.gather(*tasks, return_exceptions=True)`.
2. Each scanner returns a `ScannerResult` with `findings` list and `has_violations` flag. Scanner crashes produce `None` results (not exceptions that crash the pipeline).
3. If all scanners return `None` (total failure), the pipeline returns `fail_closed`.
4. `SafetyPolicy.evaluate()` aggregates valid results -- any violation produces a `block` decision. No violations produce `allow`.
5. Block messages come from `block_messages.py` templates, ordered by severity. **Block messages never echo the flagged content** -- only category labels and revision hints.

Two scanners are registered by default:
- `DataProtectionScanner` (Presidio) -- PII and sensitive data detection. Uses regex-based entities at 0.7 confidence threshold. NLP-dependent entities (PERSON, LOCATION) are removed to prevent false positives on Chinese text.
- `ContentGuardScanner` -- regex injection/harmful content rules + Qwen3Guard-Gen-0.6B generative model for probabilistic detection on both Chinese and English text.

### SSE Streaming

The streaming path (`POST /api/chat/stream`) uses `sse-starlette` to deliver Server-Sent Events. The flow:

1. Frontend sends request via `useStreamChat.ts` hook using `fetch()` + `EventSourceParserStream`.
2. Backend `_event_generator()` creates a manual `AsyncSession` (not `Depends`) and calls `StreamingChatService.stream_response()`.
3. The service yields SSE event dicts with `event` and `data` fields:
   - `chunk` -- clean sentence content (after output safety scan passes)
   - `blocked` -- entire output blocked (any sentence violation)
   - `done` -- stream complete with `conversation_id` and `message_id`
   - `error` -- input blocked, model error, or other failure
4. Frontend processes events: accumulates `chunk` segments into `StreamSegment[]`, handles `blocked` by showing a block message, handles `done` by storing the final response.

### Sentence Buffering

`SentenceBuffer` (in `backend/app/streaming/buffer.py`) splits model output into sentence-level chunks for safety scanning. The splitting regex matches:
- Periods not after single uppercase letters (avoid splitting abbreviations like "U.S.")
- Exclamation/question marks followed by whitespace
- Bare newlines

The buffer accumulates tokens via `add_token()` and emits complete sentences. `flush()` returns remaining content at stream end.

**Critical policy**: If any sentence in the output has a safety violation, the **entire output is blocked** -- no partial display. This is enforced in `StreamingChatService.stream_response()` which scans all sentences first, then decides to stream all clean sentences or block everything.

### Auto-Degrade Pattern

The frontend `useStreamChat` hook implements an auto-degrade pattern: if the SSE stream fails (5xx response, no response body, or timeout after 600 seconds), it falls back to the non-streaming `POST /api/chat/send` endpoint. This ensures the chat works even when SSE infrastructure has issues. A `degraded` state flag shows a notice to the user.

### Auth Flow (Mock OIDC)

The mock OIDC flow simulates a real OIDC integration for MVP development:
1. Frontend calls `POST /api/auth/login?role=employee|admin` -- backend returns `redirect_url` and signed `state_token`.
2. Frontend navigates to mock OIDC page, then calls `POST /api/auth/callback` with `state_token` and `role`.
3. Backend validates the signed token (itsdangerous TimedSerializer), creates/finds user in DB, creates a Session row, sets `session_id` cookie.
4. Subsequent requests use `get_current_user` dependency which extracts the cookie, queries the Session table, checks expiry, and returns the User object.

Session expiry is handled fail-closed: expired sessions are deleted from the DB and return 401. The frontend `AuthRestorer` component in `providers.tsx` attempts to restore session from cookie on mount.

### Repository Pattern

Domain modules use repository classes that wrap SQLAlchemy session operations:
- `ConversationRepository(session)` -- CRUD for conversations/messages, ownership-filtered
- `AuditRepository(session)` -- records audit events with metadata-only storage
- `ModelConfigRepository` -- static methods for model config CRUD with Fernet encryption
- `PolicyConfigRepository` -- static methods for scanner policy settings

Repositories are instantiated in route handlers with the injected `AsyncSession`. They call `session.flush()` (not `commit()`) within their methods -- the `get_db_session` dependency commits at the end of the request lifecycle.

## Debugging Tips

### Seeing Safety Scan Details in Console

The backend configures INFO-level logging in `main.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
)
```

Safety pipeline scans log detailed information:
- `SafetyPipeline._scan()` logs input/output scan results including action, categories, and findings summary.
- `DataProtectionScanner.scan()` logs each detected PII entity with type, score, and the matched text.
- `ContentGuardScanner.scan()` logs the guard model response, injection rule matches, and harmful content matches.

When debugging a specific scan, check the console output for lines from these loggers:
- `app.safety.pipeline` -- pipeline orchestration decisions
- `app.safety.data_protection` -- PII detection details
- `app.safety.llm_guardrails` (registered as `content_guard`) -- injection/harmful content detection
- `app.streaming.service` -- streaming sentence-level scan decisions

### Testing Streaming

To test SSE streaming manually:

1. Start both backend and frontend.
2. Open browser DevTools Network tab, filter for EventStream requests.
3. Send a chat message -- observe the `POST /api/chat/stream` request and SSE events.
4. Test block scenarios: send messages containing PII (e.g. "My SSN is 123-45-6789") or injection patterns (e.g. "Ignore all previous instructions").
5. For backend-only testing, use curl:
   ```bash
   # First, get a session cookie via mock OIDC
   curl -X POST http://localhost:8000/api/auth/login?role=employee
   # Copy state_token from response, then:
   curl -X POST http://localhost:8000/api/auth/callback?role=employee&state_token=<token> -c cookies.txt
   # Now stream a chat message:
   curl -N -X POST http://localhost:8000/api/chat/stream -b cookies.txt -H "Content-Type: application/json" -d '{"message":"Hello","model_id":"qwen-plus"}'
   ```

### Testing Safety Pipeline in Isolation

The test suite provides mock scanners that avoid loading real ML models. See `backend/app/tests/test_fixtures.py` for `MockDataProtectionScanner` and `MockLLMGuardrailScanner`.

To test the pipeline in a Python REPL:
```python
from app.safety.pipeline import SafetyPipeline
from app.safety.policy import SafetyPolicy
pipeline = SafetyPipeline(scanners=[], policy=SafetyPolicy(), timeout=30.0)
decision = await pipeline.scan_input("Hello", user_id, model_id)
# decision.action == "allow" (no scanners registered)
```

For full scanner testing, initialize `get_safety_pipeline()` which loads real scanners. Note: loading the guard model (Qwen3Guard-Gen-0.6B) takes time and requires transformers + torch.

### Testing with Dependency Overrides

The test suite uses FastAPI `dependency_overrides` to swap production dependencies with test mocks:

```python
# Override safety pipeline for tests
app.dependency_overrides[get_safety_pipeline] = get_mock_pipeline
app.dependency_overrides[get_provider_registry] = get_mock_registry
# ... run tests ...
# Clean up
app.dependency_overrides.pop(get_safety_pipeline, None)
```

See `backend/app/tests/test_chat_api.py` for the full pattern. The shared `conftest.py` overrides `get_db_session` with an in-memory SQLite session for all tests.

### Common Issues

| Issue | Cause | Fix |
|---|---|---|
| "No models available" | No model provider credentials configured | Set `QWEN_API_KEY` or `LOCAL_LLM_BASE_URL` in `APIKEY.env` or `backend/.env` |
| "Guard model loading timeout" | Qwen3Guard model download is slow | Set `HF_ENDPOINT=https://hf-mirror.com` for China mirror, or remove `ContentGuardScanner` from pipeline |
| SQLite write lock errors | Multiple concurrent writes while SSE stream holds session | WAL mode + busy_timeout are configured in `db/__init__.py`. If issues persist, check that SSE streaming commits between yields (`streaming/service.py` commits at each write boundary) |
| SpaCy model not found | `en_core_web_lg` not downloaded | Run `python -m spacy download en_core_web_lg` |
| Frontend 401 loop | Stale session cookie from previous login | Clear browser cookies, or the `AuthRestorer` component will auto-redirect to login |
| Presidio false positives on Chinese text | NLP-dependent recognizers misidentify Chinese words as PII | These recognizers are removed in `DataProtectionScanner.__init__()`. If new false positives appear, add entity types to `_NLP_ENTITIES_TO_IGNORE` in `data_protection.py` |

## Git Workflow

### Branching

- `main` is the primary branch for PRs and releases.
- Feature branches: `feat/<short-description>` (e.g., `feat/streaming-chat`, `feat/admin-audit`)
- Fix branches: `fix/<short-description>`
- Work branches: use descriptive names that reference the feature/fix

### Committing

- Commit messages should be concise and describe the change purpose.
- Use conventional commit prefixes: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`.
- Avoid committing `.env` files with real credentials. The `.gitignore` excludes `.env` and `.env.local` but keeps `.env.example`.
- The `APIKEY.env` file contains real API keys and is listed in `.gitignore` -- verify it is not being tracked.

### What Not to Commit

- `backend/.venv/` -- virtual environment (excluded in `.gitignore`)
- `backend/*.db`, `backend/*.db-shm`, `backend/*.db-wal` -- SQLite database files
- `frontend/node_modules/` -- npm dependencies
- `frontend/dist/` -- build output
- `.env` files with real credentials (only `.env.example` should be tracked)
<!-- VERIFY: Whether .env.example actually exists in the repository -->

## Where to Go Next

- **Testing details** -- see `docs/TESTING.md` for test strategy, fixture patterns, and coverage expectations (when available).
- **Architecture deep-dive** -- see `docs/ARCHITECTURE.md` for component diagrams, data flow descriptions, and key abstraction reference.
- **Configuration reference** -- see `docs/CONFIGURATION.md` for all environment variables, defaults, admin runtime configuration, and per-environment overrides.
- **API specification** -- the FastAPI app auto-generates OpenAPI docs at `http://localhost:8000/docs` (Swagger UI) when the backend is running.