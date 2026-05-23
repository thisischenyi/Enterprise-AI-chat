<!-- generated-by: gsd-doc-writer -->

# Getting Started

This guide walks you through setting up and running the Enterprise AI Chat MVP on your local machine for development.

## Prerequisites

Before you begin, install the following tools:

| Tool | Minimum Version | Purpose |
|---|---|---|
| Python | 3.12 | Backend runtime. 3.12+ is required for async performance improvements and library compatibility. <!-- VERIFY: No explicit Python version constraint file (pyproject.toml/setup.cfg) found in the repository; 3.12 is recommended per project spec but not enforced by tooling --> |
| Node.js | 20.x <!-- VERIFY: No .nvmrc or engines field in package.json; 20.x is the LTS line compatible with the Vite 8 / TypeScript 6 versions in package.json --> | Frontend runtime and build toolchain |
| npm | Comes with Node.js | Frontend package manager |
| Git | Any recent version | Version control |

Optional (for local LLM provider):

| Tool | Purpose |
|---|---|
| Ollama | Local OpenAI-compatible LLM server. Required only if you want to test with a local model instead of Qwen. |

## First-Time Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai_chat_tool
```

### 2. Backend setup

Create a Python virtual environment and install dependencies:

```bash
cd backend
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (CMD):
.venv\Scripts\activate.bat
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Download the spaCy NLP model required by the Presidio PII scanner:

```bash
python -m spacy download en_core_web_lg
```

This model is approximately 560 MB. The download may take a few minutes depending on your network speed. It is required before the backend can start -- the DataProtectionScanner will fail to initialize without it.

### 3. Frontend setup

```bash
cd frontend
npm install
```

This installs all dependencies listed in `package.json`, including React, Vite, TanStack Query, Zustand, Tailwind CSS, and Vitest.

## Environment Variables

### Backend (`backend/.env`)

Copy the example file and configure your values:

```bash
cd backend
cp .env.example .env
```

The `.env.example` file contains:

```
DATABASE_URL=sqlite+aiosqlite:///./enterprise_chat_mvp.db
SECRET_KEY=dev-secret-change-this
```

Key variables you may need to set:

| Variable | Default | When to Change |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./enterprise_chat_mvp.db` | Change to PostgreSQL URL (`postgresql+asyncpg://...`) for production or concurrent load testing. SQLite is sufficient for local development. |
| `SECRET_KEY` | `dev-secret-change-this` | Must be changed for any non-development environment. The default is intentionally weak. |
| `SPACY_MODEL` | `en_core_web_lg` | Only change if you downloaded a different spaCy model. |
| `HF_ENDPOINT` | (HuggingFace default) | Set to `https://hf-mirror.com` if you are in a region where HuggingFace is inaccessible (e.g. China). |
| `QWEN_API_KEY` | (empty) | Set to enable the Qwen/DashScope model provider. See API key configuration below. |
| `LOCAL_LLM_BASE_URL` | (empty) | Set to `http://localhost:11434/v1` if you are running Ollama locally. |
| `LOCAL_LLM_API_KEY` | `ollama` | Ollama accepts any value. Change only if your local LLM server requires authentication. |

### API key configuration (`APIKEY.env`)

Model provider API keys are stored in `APIKEY.env` at the project root (not in `backend/.env`). The backend loads this file automatically at startup (`backend/app/main.py` line 16: `load_dotenv(_project_root / "APIKEY.env")`).

Create or edit `APIKEY.env` in the project root directory:

```
DASHSCOPE_API_KEY=sk-your-key-here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3.6-plus
```

**Variable aliases:** The provider registry accepts both `QWEN_API_KEY` and `DASHSCOPE_API_KEY` for the Qwen provider. If both are set, `QWEN_API_KEY` takes priority. Similarly, `OPENAI_API_BASE` takes priority over `LOCAL_LLM_BASE_URL`, and `OPENAI_API_KEY` takes priority over `LOCAL_LLM_API_KEY`.

**At least one model provider must be configured** for chat to work. Without any provider credentials, the model list will be empty and chat messages will fail with "no models available."

### Frontend (`frontend/.env`)

The frontend `.env` file is minimal:

```
VITE_API_BASE_URL=/api
```

In development, Vite proxies `/api` requests to `http://localhost:8000` (configured in `frontend/vite.config.ts`). You do not need to change this value for local development. For production deployment, set it to the deployed backend URL.

## Running Development Servers

You need both the backend and frontend running simultaneously.

### Backend

```bash
cd backend
.venv\Scripts\Activate.ps1   # Windows PowerShell
uvicorn app.main:app --reload --port 8000
```

The `--reload` flag watches for file changes and automatically restarts the server. The backend runs on `http://localhost:8000`.

On first startup, the backend:
- Creates all database tables (SQLite file `backend/enterprise_chat_mvp.db`)
- Seeds two mock test users into the database
- Downloads the Qwen3Guard model from HuggingFace if not cached locally (this may take several minutes on first run; subsequent runs use the cached model)

Verify the backend is running:

```bash
curl http://localhost:8000/health
# Expected response: {"status":"ok"}
```

### Frontend

```bash
cd frontend
npm run dev
```

The frontend dev server runs on `http://localhost:5173` (Vite's default port). It automatically proxies `/api` requests to the backend at `http://localhost:8000`.

Open `http://localhost:5173` in your browser. You should see the login page.

## Mock OIDC Login

The MVP uses a mock OIDC provider for authentication. There is no real identity provider -- the login flow simulates OIDC with signed tokens (itsdangerous TimedSerializer).

### Login flow

1. Navigate to `http://localhost:5173/login`
2. Select a role from the dropdown: **Employee** or **Admin**
3. Click **Sign In**
4. The mock OIDC confirmation page appears. Click the confirm button to complete the callback.
5. You are redirected to the chat page.

### Mock credentials

Two pre-seeded test users are available:

| Role | Email | Name | Access |
|---|---|---|---|
| Employee | `employee@test-enterprise.com` | Test Employee | Chat page only (`/chat`) |
| Admin | `admin@test-enterprise.com` | Test Admin | Chat page (`/chat`) + Admin pages (`/admin/audit`, `/admin/models`, `/admin/policy`) |

Sessions expire after 1 hour (3600 seconds). When a session expires, you will be redirected back to the login page.

### Admin-only features

When logged in as Admin, the sidebar shows an additional **Admin** section with:
- **Audit** -- view safety scan audit events with multi-dimension filters
- **Models** -- add, edit, and delete model provider configurations (API keys are encrypted before storage)
- **Policy** -- toggle individual safety scanners and adjust sensitivity levels

These pages are protected by the `AdminRoute` guard -- non-admin users are redirected to the chat page.

## Running Tests

### Backend tests

```bash
cd backend
.venv\Scripts\Activate.ps1   # Windows PowerShell
pytest
```

Tests use an in-memory SQLite database (configured in `backend/app/tests/conftest.py`) and do not affect your development database. The test suite includes auth, safety pipeline, chat API, and role-based access tests.

### Frontend tests

```bash
cd frontend
npm run test          # single run
npm run test:watch    # watch mode
```

Tests use Vitest with jsdom environment (configured in `frontend/vitest.config.ts`).

## Common First-Run Problems

### "No models available" or empty model dropdown

**Cause:** No model provider credentials are configured.

**Fix:** Set `DASHSCOPE_API_KEY` or `QWEN_API_KEY` in `APIKEY.env` (for Qwen), or set `LOCAL_LLM_BASE_URL` in `backend/.env` (for a local LLM). At least one provider must be configured. Verify by checking `http://localhost:8000/api/chat/models` -- it should return a non-empty list.

### SpaCy model not found / Presidio initialization error

**Cause:** The `en_core_web_lg` spaCy model was not downloaded.

**Fix:** Run `python -m spacy download en_core_web_lg` inside the activated backend virtual environment. Verify with `python -c "import spacy; spacy.load('en_core_web_lg')"`.

### Qwen3Guard model download hangs or fails

**Cause:** The guard model (`Qwen/Qwen3Guard-Gen-0.6B`, approximately 1.2 GB) is downloaded from HuggingFace on first scanner initialization. Network issues or HuggingFace accessibility blocks can prevent the download.

**Fix:** Set `HF_ENDPOINT=https://hf-mirror.com` in `backend/.env` if you are in a region where HuggingFace is inaccessible. The model is cached by the `transformers` library after the first successful download -- subsequent runs will not re-download it.

### Session cookie not working / "Not authenticated" after login

**Cause:** The frontend and backend are running on different ports without the Vite proxy. Or the backend `SECRET_KEY` changed between runs (which invalidates previously signed session tokens).

**Fix:** Make sure you access the frontend at `http://localhost:5173` (not directly at `http://localhost:8000`). The Vite dev server proxies API calls to the backend. If `SECRET_KEY` in `backend/.env` changed, clear your browser cookies and log in again.

### Database locked errors on concurrent requests

**Cause:** SQLite write contention under concurrent access (e.g. multiple SSE streams writing simultaneously).

**Fix:** The backend already configures SQLite with WAL mode and a 30-second busy timeout (`backend/app/db/__init__.py`). If you still encounter lock errors under heavy concurrent use, switch to PostgreSQL by setting `DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname` in `backend/.env`. <!-- VERIFY: PostgreSQL setup instructions (creating the database, running migrations) are not detailed in the repository -->.

### Virtual environment not activating on Windows PowerShell

**Cause:** PowerShell execution policy may block running the activation script.

**Fix:** Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in an administrator PowerShell session, then activate the virtual environment with `.venv\Scripts\Activate.ps1`.

### Frontend proxy errors (CORS or 502)

**Cause:** The backend is not running, or it is running on a different port than `8000`.

**Fix:** Start the backend first (`uvicorn app.main:app --reload --port 8000`). If you need a different port, update the `proxy` target in `frontend/vite.config.ts` to match.

## Where to Go Next

- **[ARCHITECTURE.md](ARCHITECTURE.md)** -- understand the system design, data flow, and key abstractions
- **[CONFIGURATION.md](CONFIGURATION.md)** -- full reference for all environment variables, defaults, admin runtime configuration, and safety scanner settings