<!-- generated-by: gsd-doc-writer -->
# Configuration

This document covers all configuration options for the Enterprise AI Chat MVP, including environment variables, config file formats, required vs optional settings, default values, and per-environment overrides.

## Environment Variables

### Backend (Python / FastAPI)

Variables are loaded from `backend/.env` via `python-dotenv` at startup (`backend/app/db/__init__.py` calls `load_dotenv()`).

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Optional | `sqlite+aiosqlite:///./enterprise_chat_mvp.db` | SQLAlchemy async connection string. Use `sqlite+aiosqlite:///./file.db` for SQLite or `postgresql+asyncpg://user:pass@host/db` for PostgreSQL. |
| `SECRET_KEY` | Optional | `dev-secret-change-this` | Session token signing key (itsdangerous TimedSerializer). **Must be changed in production** — the default is for development only. |
| `ENCRYPTION_KEY` | Optional | Derived from `SECRET_KEY` | Fernet encryption key for admin-stored model API keys. If not set, a key is derived from `SECRET_KEY` by padding/truncating to 32 bytes and base64-encoding. **Must be set explicitly in production** to avoid key derivation from a weak `SECRET_KEY`. |
| `SPACY_MODEL` | Optional | `en_core_web_lg` | spaCy NLP model used by Presidio AnalyzerEngine for PII detection. Must be a model compatible with Presidio's context-aware scoring. |
| `HF_ENDPOINT` | Optional | (HuggingFace default) | HuggingFace mirror endpoint URL. Used when downloading the guard model in regions where HuggingFace is inaccessible (e.g. `https://hf-mirror.com` for China). |
| `DASHSCOPE_API_KEY` | Optional | (empty) | Alibaba DashScope API key for Qwen model access. Accepted as an alias for `QWEN_API_KEY` — either one enables the Qwen provider. |
| `QWEN_API_KEY` | Optional | (empty) | Qwen/DashScope API key. Takes priority over `DASHSCOPE_API_KEY` if both are set. Required if you want to use Qwen models via environment-based provider discovery. |
| `QWEN_BASE_URL` | Optional | `https://dashscope.aliyuncs.com/compatible-mode/v1` | Qwen API endpoint URL (OpenAI-compatible mode). |
| `QWEN_MODEL` | Optional | `qwen-plus` | Qwen model identifier (e.g. `qwen-plus`, `qwen-max`, `qwen3.6-plus`). |
| `OPENAI_API_BASE` | Optional | (empty) | OpenAI-compatible endpoint base URL. Accepted as an alias for `LOCAL_LLM_BASE_URL` — takes priority if both are set. Required if you want to use a local/OpenAI-compatible model provider. |
| `LOCAL_LLM_BASE_URL` | Optional | (empty) | Local OpenAI-compatible LLM endpoint URL (e.g. `http://localhost:11434/v1` for Ollama). Used as fallback if `OPENAI_API_BASE` is not set. |
| `OPENAI_API_KEY` | Optional | (empty) | API key for the OpenAI-compatible endpoint. Accepted as an alias for `LOCAL_LLM_API_KEY` — takes priority if both are set. |
| `LOCAL_LLM_API_KEY` | Optional | `ollama` | API key for local LLM endpoint. Used as fallback if `OPENAI_API_KEY` is not set. Ollama typically accepts any value. |
| `OPENAI_MODEL_NAME` | Optional | (empty) | Model ID for the OpenAI-compatible provider. Takes priority over `LOCAL_LLM_MODEL_ID`. Falls back to `LOCAL_LLM_MODEL_ID` default. |
| `LOCAL_LLM_MODEL_ID` | Optional | `local-model` | Model identifier for the local LLM provider. Used as fallback if `OPENAI_MODEL_NAME` is not set. |
| `GUARD_MODEL` | Optional | `Qwen/Qwen3Guard-Gen-0.6B` | HuggingFace model path for the generative content guard scanner. Loaded via `transformers` AutoModelForCausalLM. |

### Frontend (React / Vite)

Variables are loaded from `frontend/.env` via Vite's built-in env handling (exposed as `import.meta.env.VITE_*`).

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Optional | `/api` | Base URL for backend API calls. In development, Vite proxies `/api` to `http://localhost:8000` (configured in `vite.config.ts`). In production, set this to the deployed backend URL. |

## Config File Format

The project does not use a separate config file (JSON, YAML, TOML) for application settings. All runtime configuration is through environment variables loaded by `python-dotenv` on the backend and Vite on the frontend.

### `.env` file structure

Both backend and frontend use `.env` files for local development:

```
# backend/.env — Python dotenv format
DATABASE_URL=sqlite+aiosqlite:///./enterprise_chat_mvp.db
SECRET_KEY=dev-secret-change-this
QWEN_API_KEY=sk-your-key-here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_API_KEY=ollama
SPACY_MODEL=en_core_web_lg
HF_ENDPOINT=https://hf-mirror.com

# frontend/.env — Vite env format (only VITE_* prefix is exposed to client)
VITE_API_BASE_URL=/api
```

The canonical list of backend variables is documented in `backend/.env.example`. Copy it to `backend/.env` and fill in your values.

## Required vs Optional Settings

### Required for production deployment

These settings have development defaults but **must be changed** for any non-development environment:

- **`SECRET_KEY`** — The default `dev-secret-change-this` is only for local development. In production, set a cryptographically random string. Failure to change it allows anyone to forge session tokens.
- **`ENCRYPTION_KEY`** — If not set, a Fernet key is derived from `SECRET_KEY` by padding to 32 bytes. This is acceptable for MVP development but **must be set to a proper Fernet key** in production for secure API key storage via the admin model config feature. Generate one with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- **At least one model provider credential** — Either `QWEN_API_KEY` (or `DASHSCOPE_API_KEY`) for Qwen, or `OPENAI_API_BASE` (or `LOCAL_LLM_BASE_URL`) for a local LLM. Without any provider credentials, the ProviderRegistry will have zero models and chat will not function.

### Optional with meaningful defaults

- `DATABASE_URL` defaults to SQLite, which is suitable for MVP development. PostgreSQL is recommended for production concurrent access.
- `GUARD_MODEL` defaults to `Qwen/Qwen3Guard-Gen-0.6B`. The model is downloaded at scanner initialization time from HuggingFace (or `HF_ENDPOINT` if set).
- `SPACY_MODEL` defaults to `en_core_web_lg`. Must be downloaded before first run: `python -m spacy download en_core_web_lg`.

## Defaults

| Variable | Default Value | Where Set |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./enterprise_chat_mvp.db` | `backend/app/db/__init__.py` line 15 |
| `SECRET_KEY` | `dev-secret-change-this` | `backend/app/auth/oidc.py` line 46 |
| `ENCRYPTION_KEY` | Derived from `SECRET_KEY` (padded to 32 bytes, base64-encoded) | `backend/app/admin/models_repo.py` lines 15-22 |
| `SPACY_MODEL` | `en_core_web_lg` | `backend/app/safety/data_protection.py` line 70 |
| `QWEN_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `backend/app/models/providers.py` line 51 |
| `QWEN_MODEL` | `qwen-plus` | `backend/app/models/providers.py` line 55 |
| `LOCAL_LLM_API_KEY` | `ollama` | `backend/app/models/providers.py` line 64 |
| `LOCAL_LLM_MODEL_ID` | `local-model` | `backend/app/models/providers.py` line 65 |
| `GUARD_MODEL` | `Qwen/Qwen3Guard-Gen-0.6B` | `backend/app/safety/llm_guardrails.py` line 127 |
| `VITE_API_BASE_URL` | `/api` | `frontend/src/lib/api.ts` line 3 |
| Safety pipeline timeout | 30 seconds | `backend/app/safety/pipeline.py` line 31 |
| Presidio score threshold | 0.7 | `backend/app/safety/data_protection.py` line 123 |
| SQLite WAL busy_timeout | 30000 ms | `backend/app/db/__init__.py` line 33 |
| SQLite synchronous | `NORMAL` | `backend/app/db/__init__.py` line 34 |
| Session token max age | 3600 seconds (1 hour) | `backend/app/auth/oidc.py` line 47 |
| Policy sensitivity | `medium` | `backend/app/admin/policy_repo.py` line 26 |
| Guard model max_new_tokens | 128 | `backend/app/safety/llm_guardrails.py` line 188 |

## Per-Environment Overrides

### Development

- `backend/.env` — Python dotenv file, loaded at import time via `load_dotenv()` in `backend/app/db/__init__.py`.
- `frontend/.env` — Vite env file, only variables prefixed `VITE_` are exposed to the client bundle.
- Vite dev server proxies `/api` requests to `http://localhost:8000` (configured in `frontend/vite.config.ts`), so `VITE_API_BASE_URL=/api` works for local development without CORS issues.

### Production

- **Environment variables** should be set via the hosting platform's secret/environment manager (not `.env` files).
- `DATABASE_URL` must be changed to PostgreSQL: `postgresql+asyncpg://user:password@host:5432/dbname`.
- `SECRET_KEY` and `ENCRYPTION_KEY` must be set to production-grade values.
- `VITE_API_BASE_URL` must be set to the deployed backend URL (e.g. `https://api.example.com/api`).
- SQLite pragmas (WAL mode, busy_timeout, synchronous) only apply when `DATABASE_URL` starts with `sqlite` — they are automatically skipped for PostgreSQL (`backend/app/db/__init__.py` lines 19, 28).

### Testing

- No `.env.test` file exists in the repository. Tests use the default SQLite configuration.
- The Alembic migration environment reads `DATABASE_URL` from `os.getenv("DATABASE_URL")` (`backend/alembic/env.py` line 21) without a fallback default.

<!-- VERIFY: Production PostgreSQL connection string format and hosting platform secret manager details are not defined in the repository -->

## Admin Runtime Configuration

Beyond environment variables, the system provides admin-only API endpoints for runtime configuration. These are accessible only to users with the `admin` role (enforced by `Depends(get_admin_user)`).

### Model Configuration (`/api/admin/models`)

Admins can add, update, and delete model providers at runtime via CRUD endpoints. Model API keys are encrypted with Fernet before storage and masked (showing only last 4 characters) in API responses.

| Endpoint | Method | Description |
|---|---|---|
| `/api/admin/models` | GET | List all model configs (API keys masked) |
| `/api/admin/models` | POST | Create a new model config |
| `/api/admin/models/{model_id}` | PUT | Update a model config |
| `/api/admin/models/{model_id}` | DELETE | Delete a model config |

**Create model request fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string (max 100) | Yes | Display name for the model |
| `provider_type` | string (`qwen` or `openai_compatible`) | Yes | Provider type identifier |
| `endpoint_url` | string (max 500) | Yes | API endpoint URL |
| `model_id` | string (max 100) | Yes | Model identifier (unique) |
| `api_key` | string (min 1) | Yes | Raw API key (encrypted before storage) |
| `enabled` | boolean | No (default: true) | Whether the model is active |

### Policy Configuration (`/api/admin/policy`)

Admins can toggle individual scanners and adjust sensitivity levels per scanner name.

| Endpoint | Method | Description |
|---|---|---|
| `/api/admin/policy` | GET | List all scanner policies |
| `/api/admin/policy/{scanner_name}` | PUT | Update a scanner policy |

**Default scanners seeded on first access:**

| Scanner Name | Default Enabled | Default Sensitivity |
|---|---|---|
| `pii_detection` | true | medium |
| `prompt_injection` | true | medium |
| `jailbreak` | true | medium |
| `toxicity` | true | medium |
| `ban_topics` | true | medium |

**Update policy request fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `enabled` | boolean | Yes | Whether this scanner is active |
| `sensitivity` | string (`low`, `medium`, `high`) | Yes | Detection sensitivity level |

<!-- VERIFY: Whether policy sensitivity (low/medium/high) currently affects scanner thresholds or is stored but not yet applied to scanner behavior -->

## Safety Scanner Configuration Details

### DataProtectionScanner (Presidio)

- **Engine**: Microsoft Presidio AnalyzerEngine with spaCy NLP (`en_core_web_lg` by default).
- **Entity types scanned**: Only regex-detectable entities — `EMAIL_ADDRESS`, `PHONE_NUMBER`, `US_SSN`, `CREDIT_CARD`, `IBAN_CODE`, `IP_ADDRESS`, `US_DRIVER_LICENSE`, `US_PASSPORT`, `CHINESE_NATIONAL_ID`, `INCOME`, `EMPLOYEE_ID`, `PROJECT_CODE`.
- **NLP-dependent entities excluded**: `PERSON`, `LOCATION`, `DATE_TIME`, `NRP`, `AGE`, `ORGANIZATION`, and others are removed from the analyzer registry to prevent false positives on Chinese/mixed-language text.
- **Score threshold**: 0.7 — only matches with confidence >= 0.7 are reported as findings.
- **Custom recognizers**: Four enterprise-specific recognizers registered at initialization:
  - `EmployeeIdRecognizer` — detects `EMP-XXXX` pattern
  - `ProjectCodeRecognizer` — detects `PRJ-XXXX` pattern
  - `ChineseNationalIdRecognizer` — detects 18-digit IDs with checksum validation
  - `IncomeRecognizer` — detects salary amounts near salary keywords (Chinese + English)

### ContentGuardScanner (LLM Guardrails)

- **Rule-based detection**: Two regex rule sets compiled at module load:
  - Injection rules (`_INJECTION_RULES`): 14 English patterns + 7 Chinese patterns covering instruction override, identity manipulation, safety bypass, and system/internal access.
  - Harmful content rules (`_HARMFUL_CONTENT_RULES`): 4 English patterns + 5 Chinese patterns covering hate/discrimination requests.
- **Generative guard model**: Qwen3Guard-Gen-0.6B loaded via HuggingFace `transformers`. Scans content the regex rules do not cover. Produces structured safe/unsafe + category responses. Works on both Chinese and English text.
- **Category mapping**: Guard model output categories (English and Chinese) are mapped to internal `RiskCategory` enum values.

### SafetyPipeline

- **Timeout**: 30 seconds. If all scanners do not complete within this window, the pipeline returns a `fail_closed` decision.
- **Fail-closed semantics**: Scanner crash or timeout results in blocking the content with a generic system error message. No content is ever displayed when a scanner fails.
- **Parallel execution**: All registered scanners run in parallel via `asyncio.gather`. Individual scanner failures do not block other scanners.

## SQLite Configuration

When `DATABASE_URL` starts with `sqlite`, three pragmas are applied on every connection (`backend/app/db/__init__.py`):

| PRAGMA | Value | Purpose |
|---|---|---|
| `journal_mode` | `WAL` | Write-Ahead Logging allows concurrent reads while a writer holds the lock. Essential for SSE streaming which holds connections for extended periods. |
| `busy_timeout` | `30000` (30 seconds) | How long SQLite waits for a locked database before raising an error. Prevents immediate failures during concurrent writes. |
| `synchronous` | `NORMAL` | Balance between write safety and speed. WAL mode with NORMAL synchronous is safe enough for MVP use; FULL is slower. |

These pragmas are **not applied** when `DATABASE_URL` uses PostgreSQL.