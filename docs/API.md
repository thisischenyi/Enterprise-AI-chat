<!-- generated-by: gsd-doc-writer -->

# Enterprise AI Chat MVP — API Reference

Base URL: `http://localhost:8000` (local development)

All endpoints are prefixed with `/api` as shown below. The application is a FastAPI service; interactive docs are available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

## Authentication

All endpoints except `/health`, `/api/auth/login`, and `/api/auth/callback` require authentication via a session cookie (`session_id`) set by the mock OIDC callback flow.

| Mechanism | Detail |
|-----------|--------|
| Cookie name | `session_id` |
| Cookie properties | `httponly=True`, `samesite=lax`, `max_age=3600` (1 hour) |
| Token validation | Signed with `itsdangerous.TimedSerializer`; stored in DB `sessions` table; expiry checked on every request |
| Unauthenticated | Returns `401 Unauthorized` with `detail: "Not authenticated"` |
| Expired session | Returns `401 Unauthorized` with `detail: "Session expired"` |
| Invalid session | Returns `401 Unauthorized` with `detail: "Invalid session"` |
| Admin-only endpoints | Returns `403 Forbidden` with `detail: "Admin access required"` (no role enumeration hints) |

---

## Health Check

### `GET /health`

Unauthenticated. Returns service health status.

**Response** `200 OK`:

```json
{
  "status": "ok"
}
```

---

## Auth Endpoints

Prefix: `/api/auth`

### `POST /api/auth/login`

Initiate mock OIDC login flow. Unauthenticated.

**Query Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `role` | `string` | `"employee"` | Mock user role. Must be `"employee"` or `"admin"` |

**Success Response** `200 OK`:

```json
{
  "redirect_url": "/mock-login",
  "state_token": "<signed-state-token>",
  "role": "employee"
}
```

**Error Response** `400 Bad Request` (invalid role):

```json
{
  "detail": "Invalid role: manager. Must be 'employee' or 'admin'."
}
```

### `POST /api/auth/callback`

Mock OIDC callback. Validates state token, creates/finds user, creates session, sets session cookie. Unauthenticated (this is the login completion step).

**Query Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `role` | `string` | `"employee"` | Role to assign for this mock login |
| `state_token` | `string` | `""` | Signed state token from `/login` response |

**Success Response** `200 OK`:

Sets cookie `session_id=<signed-session-token>` and returns:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "employee@test-enterprise.com",
  "name": "Test Employee",
  "role": "employee"
}
```

Mock user identities per role:

| Role | Email | Name |
|------|-------|------|
| `employee` | `employee@test-enterprise.com` | `Test Employee` |
| `admin` | `admin@test-enterprise.com` | `Test Admin` |

**Error Response** `401 Unauthorized` (invalid/expired state token):

```json
{
  "detail": "Invalid state token"
}
```

```json
{
  "detail": "State token expired"
}
```

### `GET /api/auth/me`

Return current authenticated user identity. **Requires authentication**.

**Success Response** `200 OK`:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "employee@test-enterprise.com",
  "name": "Test Employee",
  "role": "employee"
}
```

---

## Chat Endpoints

Prefix: `/api/chat`

All chat endpoints require authentication.

### `POST /api/chat/send`

Send a chat message through the full safety pipeline: input scan -> model call -> output scan. Records audit events for every decision.

**Request Body** (`ChatRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | `string` | Yes | User message text. Min length 1. |
| `model_id` | `string` | Yes | ID of the model to use (must exist in `ProviderRegistry`) |
| `conversation_id` | `string | null` | No | UUID of existing conversation to continue. Omit to start a new conversation. |

**Request Example**:

```json
{
  "message": "What is the company policy on remote work?",
  "model_id": "qwen-plus",
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response Body** (`ChatResponse`):

| Field | Type | Description |
|-------|------|-------------|
| `status` | `"allowed" \| "blocked" \| "fail_closed"` | Pipeline decision |
| `content` | `string` | For `allowed`: model response. For `blocked`: category-specific block message (never echoes detected content). For `fail_closed`: generic error message. |
| `model_id` | `string | null` | Provider model ID (only for `allowed`) |
| `provider_id` | `string | null` | Provider identifier (only for `allowed`) |
| `risk_categories` | `list[string] | null` | Risk categories that triggered the block. Values: `"pii"`, `"sensitive_data"`, `"prompt_injection"`, `"jailbreak"`, `"harmful_content"`, `"compliance"` |
| `revision_hint` | `string | null` | Guidance for user to revise (only for `blocked`) |
| `conversation_id` | `string | null` | UUID of the conversation |
| `message_id` | `string | null` | UUID of the assistant message (only for `allowed`) |

**Response Example — Allowed** `200 OK`:

```json
{
  "status": "allowed",
  "content": "The company allows remote work up to 3 days per week...",
  "model_id": "qwen-plus",
  "provider_id": "qwen",
  "risk_categories": null,
  "revision_hint": null,
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901"
}
```

**Response Example — Blocked (input)** `200 OK`:

```json
{
  "status": "blocked",
  "content": "您的消息因包含个人或敏感信息而被拦截。 请移除个人敏感信息后重试。",
  "model_id": null,
  "provider_id": null,
  "risk_categories": ["pii"],
  "revision_hint": "Please revise your message to avoid sensitive content.",
  "conversation_id": null,
  "message_id": null
}
```

**Response Example — Blocked (output)** `200 OK`:

```json
{
  "status": "blocked",
  "content": "回复因包含有害或不当内容而被拦截。 请尝试其他问题。",
  "model_id": null,
  "provider_id": null,
  "risk_categories": ["harmful_content"],
  "revision_hint": "The model response contained content that violates safety policies.",
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message_id": null
}
```

**Response Example — Fail-closed** `200 OK`:

```json
{
  "status": "fail_closed",
  "content": "Your message could not be processed due to a system error. Please try again later.",
  "model_id": null,
  "provider_id": null,
  "risk_categories": null,
  "revision_hint": null,
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message_id": null
}
```

**Error Responses**:

| Status | Condition | Detail |
|--------|-----------|--------|
| `400` | `model_id` not in registry | `"Model '<model_id>' not available"` |
| `403` | `conversation_id` belongs to another user | `"Access denied"` |

### `GET /api/chat/models`

Return available model providers with valid credentials. **Requires authentication**.

**Success Response** `200 OK`:

Returns a list of `ModelInfo` objects:

```json
[
  {
    "id": "qwen-plus",
    "name": "Qwen Plus",
    "description": "Alibaba Cloud Qwen large language model"
  },
  {
    "id": "local-model",
    "name": "Local LLM",
    "description": "Local OpenAI-compatible model endpoint"
  }
]
```

The list contents depend on environment variables. Available when credentials are present:

| Provider | Required env vars | Default model_id |
|----------|-------------------|-------------------|
| Qwen (DashScope) | `QWEN_API_KEY` or `DASHSCOPE_API_KEY` | `qwen-plus` (via `QWEN_MODEL`) |
| OpenAI-compatible | `OPENAI_API_BASE` or `LOCAL_LLM_BASE_URL` | `local-model` (via `OPENAI_MODEL_NAME` or `LOCAL_LLM_MODEL_ID`) |

---

## Streaming Chat Endpoint

Prefix: `/api/chat`

### `POST /api/chat/stream`

Stream chat response with sentence-buffered safety scanning. **Requires authentication**.

Returns a Server-Sent Events (SSE) stream via `EventSourceResponse`. The streaming service orchestrates: input scan -> model call -> sentence-buffered output scan -> SSE events.

**Request Body** (`ChatStreamRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | `string` | Yes | User message text. Min length 1. |
| `model_id` | `string` | Yes | ID of the model to use |
| `conversation_id` | `string | null` | No | UUID of existing conversation to continue |

**Request Example**:

```json
{
  "message": "Explain the safety pipeline architecture",
  "model_id": "qwen-plus",
  "conversation_id": null
}
```

### SSE Event Types

All event `data` fields are JSON-encoded strings. The client must parse `data` as JSON.

#### `chunk` — Clean output sentence

Streamed sentence-by-sentence for allowed content. Each `chunk` event contains one sentence (split on sentence-ending punctuation: `.`, `!`, `?` followed by whitespace, or bare `\n`).

```
event: chunk
data: {"content": "The safety pipeline scans "}
```

```
event: chunk
data: {"content": "both input and output.\n"}
```

#### `blocked` — Entire output blocked by safety policy

Per project spec: if any sentence in the model output triggers a policy violation, the **entire** output is blocked. No partial display or redaction. The block message uses category-specific templates and never echoes detected content.

```
event: blocked
data: {"message": "回复因包含有害或不当内容而被拦截。 请尝试其他问题。", "categories": ["harmful_content"], "conversation_id": "a1b2c3d4-...", "message_id": "b2c3d4e5-..."}
```

| Data Field | Type | Description |
|------------|------|-------------|
| `message` | `string` | Category-specific block message (highest-severity category template + revision hint) |
| `categories` | `list[string]` | Risk categories from output scan. Values: `"pii"`, `"sensitive_data"`, `"prompt_injection"`, `"jailbreak"`, `"harmful_content"`, `"compliance"` |
| `conversation_id` | `string` | UUID of the conversation |
| `message_id` | `string` | UUID of the blocked message stored in DB |

#### `done` — Stream completed successfully

Sent after all clean sentences have been streamed. Marks the end of the SSE stream.

```
event: done
data: {"conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "message_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901"}
```

| Data Field | Type | Description |
|------------|------|-------------|
| `conversation_id` | `string` | UUID of the conversation |
| `message_id` | `string` | UUID of the stored assistant message |

#### `error` — Input blocked, model error, or fail-closed

Sent when input scan blocks the message, the model provider call fails, or the pipeline enters fail-closed state. After this event the stream ends.

```
event: error
data: {"message": "您的消息因包含个人或敏感信息而被拦截。 请移除个人敏感信息后重试。"}
```

Input blocked by fail-closed:

```
event: error
data: {"message": "系统处理异常，请稍后重试。"}
```

Model provider unavailable:

```
event: error
data: {"message": "模型 'unknown-model' 不可用"}
```

```
event: error
data: {"message": "模型服务异常"}
```

| Data Field | Type | Description |
|------------|------|-------------|
| `message` | `string` | Human-readable error or block message. Language depends on context: block messages use Chinese templates; model errors use Chinese short messages. |

### SSE Stream Lifecycle

1. Client sends `POST /api/chat/stream` with JSON body
2. Server returns `EventSourceResponse` (SSE stream)
3. **If input is blocked**: single `error` event, stream ends
4. **If model call succeeds and output is clean**: multiple `chunk` events followed by `done`
5. **If model call succeeds but output has violations**: single `blocked` event (no `chunk` events sent), stream ends
6. **If model provider fails**: single `error` event, stream ends

---

## Conversation Endpoints

Prefix: `/api/conversations`

All conversation endpoints require authentication. Users can only access their own conversations.

### `GET /api/conversations`

List conversations for the current user, ordered by `updated_at` descending.

**Success Response** `200 OK`:

Returns a list of `ConversationSummary` objects:

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "What is the company policy on remote work?",
    "model_id": "qwen-plus",
    "updated_at": "2025-01-15T10:30:00"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | UUID of the conversation |
| `title` | `string` | Conversation title (first 50 chars of the initial user message) |
| `model_id` | `string` | Model used for this conversation |
| `updated_at` | `string` | ISO 8601 timestamp of last update |

### `GET /api/conversations/{conversation_id}/messages`

Get messages for a specific conversation. Returns `403` if the user does not own the conversation.

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `conversation_id` | `string (UUID)` | UUID of the conversation |

**Success Response** `200 OK`:

Returns a list of `MessageResponse` objects, ordered by `created_at` ascending:

```json
[
  {
    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "role": "user",
    "content": "What is the company policy on remote work?",
    "extra": null,
    "created_at": "2025-01-15T10:30:00"
  },
  {
    "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "role": "assistant",
    "content": "The company allows remote work up to 3 days per week...",
    "extra": null,
    "created_at": "2025-01-15T10:30:05"
  },
  {
    "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
    "role": "blocked",
    "content": "回复因包含有害或不当内容而被拦截。 请尝试其他问题。",
    "extra": {"risk_categories": ["harmful_content"]},
    "created_at": "2025-01-15T10:35:00"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | UUID of the message |
| `role` | `string` | Message role: `"user"`, `"assistant"`, `"blocked"`, `"system"`, `"tool"` |
| `content` | `string` | Message content. For `blocked` role: block message (never raw model output) |
| `extra` | `dict | null` | Additional metadata. For `blocked` messages: `{"risk_categories": [...]}` |
| `created_at` | `string` | ISO 8601 timestamp |

**Error Response** `403 Forbidden`:

```json
{
  "detail": "Access denied"
}
```

This is also returned if the conversation does not exist (no distinction to prevent enumeration).

---

## Admin Endpoints

Prefix: `/api/admin`

All admin endpoints require both authentication and `role: "admin"`. Non-admin users receive `403 Forbidden` with `detail: "Admin access required"`.

### `GET /api/admin/config`

Admin configuration placeholder endpoint.

**Success Response** `200 OK`:

```json
{
  "message": "Admin configuration endpoint - Phase 4",
  "user_role": "admin"
}
```

### `GET /api/admin/audit`

Paginated audit events with multi-dimension filters.

**Query Parameters**:

| Name | Type | Default | Constraints | Description |
|------|------|---------|-------------|-------------|
| `time_range` | `string` | `"today"` | `"today" \| "7d" \| "30d"` | Time window for events |
| `user_id` | `string | null` | `null` | — | Filter by user UUID |
| `model_id` | `string | null` | `null` | — | Filter by model ID |
| `action` | `string | null` | `null` | — | Filter by policy action (`"allow"`, `"block"`, `"fail_closed"`) |
| `risk_category` | `string | null` | `null` | — | Filter by risk category (JSON containment query) |
| `page` | `int` | `1` | `>= 1` | Page number |
| `page_size` | `int` | `20` | `1–100` | Items per page |

**Success Response** `200 OK` (`PaginatedAuditResponse`):

```json
{
  "events": [
    {
      "event_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
      "timestamp": "2025-01-15T10:30:00",
      "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "model_id": "qwen-plus",
      "source": "input",
      "risk_categories": ["pii"],
      "policy_action": "block",
      "scanner_findings": {"scanner": "DataProtectionScanner", "categories": ["pii"]}
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

| Field (per event) | Type | Description |
|--------------------|------|-------------|
| `event_id` | `UUID string` | Unique event identifier |
| `timestamp` | `datetime string` | ISO 8601 event timestamp |
| `user_id` | `UUID string` | User who triggered the event |
| `model_id` | `string` | Model involved |
| `source` | `string` | `"input"` or `"output"` |
| `risk_categories` | `list[string]` | Risk categories detected |
| `policy_action` | `string` | `"allow"`, `"block"`, or `"fail_closed"` |
| `scanner_findings` | `dict` | Anonymized metadata only — never raw content or PII values |

### `GET /api/admin/audit/stats`

Audit statistics for dashboard cards.

**Query Parameters**:

| Name | Type | Default | Constraints | Description |
|------|------|---------|-------------|-------------|
| `time_range` | `string` | `"today"` | `"today" \| "7d" \| "30d"` | Time window for statistics |

**Success Response** `200 OK` (`AuditStats`):

```json
{
  "total_events": 142,
  "total_blocks": 23,
  "block_rate_percent": 16.2,
  "most_active_user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "daily_counts_7d": [
    {"date": "2025-01-09", "count": 18},
    {"date": "2025-01-10", "count": 22},
    {"date": "2025-01-11", "count": 15},
    {"date": "2025-01-12", "count": 20},
    {"date": "2025-01-13", "count": 25},
    {"date": "2025-01-14", "count": 19},
    {"date": "2025-01-15", "count": 23}
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `total_events` | `int` | Total audit events in time range |
| `total_blocks` | `int` | Total blocked + fail-closed events |
| `block_rate_percent` | `float` | Percentage of events that were blocked (rounded to 1 decimal) |
| `most_active_user_id` | `string | null` | UUID of the user with most events |
| `daily_counts_7d` | `list[DailyCount]` | 7-day sparkline data (always 7 entries regardless of `time_range`) |

Each `DailyCount`:

| Field | Type | Description |
|-------|------|-------------|
| `date` | `string` | Date in `YYYY-MM-DD` format |
| `count` | `int` | Number of events on that date |

---

### Model Config CRUD

#### `GET /api/admin/models`

List all model configurations. API keys are returned masked (last 4 characters visible).

**Success Response** `200 OK`:

```json
[
  {
    "id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
    "name": "Qwen Plus",
    "provider_type": "qwen",
    "endpoint_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model_id": "qwen-plus",
    "api_key_masked": "••••abcd",
    "enabled": true,
    "created_at": "2025-01-15T08:00:00"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string (UUID)` | Config record UUID |
| `name` | `string` | Display name (max 100 chars) |
| `provider_type` | `string` | `"qwen"` or `"openai_compatible"` |
| `endpoint_url` | `string` | API endpoint URL (max 500 chars) |
| `model_id` | `string` | Model identifier (max 100 chars, unique) |
| `api_key_masked` | `string` | Masked API key — shows `"••••"` plus last 4 chars of decrypted key. If decryption fails: `"••••****"` |
| `enabled` | `bool` | Whether the model is active |
| `created_at` | `string` | ISO 8601 creation timestamp |

#### `POST /api/admin/models`

Create a new model configuration. API key is encrypted with Fernet before storage.

**Request Body** (`CreateModelRequest`):

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | `string` | Yes | max 100 chars | Display name |
| `provider_type` | `string` | Yes | `"qwen" \| "openai_compatible"` | Provider type |
| `endpoint_url` | `string` | Yes | max 500 chars | API endpoint URL |
| `model_id` | `string` | Yes | max 100 chars | Model identifier |
| `api_key` | `string` | Yes | min 1 char | Raw API key (encrypted before storage) |
| `enabled` | `bool` | No | default `true` | Whether model is active |

**Request Example**:

```json
{
  "name": "Qwen Plus",
  "provider_type": "qwen",
  "endpoint_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "model_id": "qwen-plus",
  "api_key": "sk-abcdef1234567890",
  "enabled": true
}
```

**Success Response** `201 Created`:

Returns `ModelConfigResponse` (same schema as GET item above).

#### `PUT /api/admin/models/{model_id}`

Update an existing model configuration. Only fields present in the request body are updated; omitted fields are unchanged. If `api_key` is omitted or null, the existing encrypted key is preserved.

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `model_id` | `UUID` | Config record UUID (not the `model_id` string field) |

**Request Body** (`UpdateModelRequest`):

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | `string | null` | No | max 100 chars | New display name |
| `provider_type` | `string | null` | No | `"qwen" \| "openai_compatible"` | New provider type |
| `endpoint_url` | `string | null` | No | max 500 chars | New endpoint URL |
| `model_id` | `string | null` | No | max 100 chars | New model identifier |
| `api_key` | `string | null` | No | — | New raw API key. Omit/null to keep existing key. |
| `enabled` | `bool | null` | No | — | Toggle enabled status |

**Request Example**:

```json
{
  "name": "Qwen Plus (Updated)",
  "enabled": false
}
```

**Success Response** `200 OK`:

Returns `ModelConfigResponse`.

**Error Response** `404 Not Found`:

```json
{
  "detail": "Model not found"
}
```

#### `DELETE /api/admin/models/{model_id}`

Delete a model configuration.

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `model_id` | `UUID` | Config record UUID |

**Success Response** `204 No Content`:

No response body.

**Error Response** `404 Not Found`:

```json
{
  "detail": "Model not found"
}
```

---

### Policy Config CRUD

#### `GET /api/admin/policy`

List all scanner policy configurations. On first access, seeds default policies if none exist.

**Success Response** `200 OK`:

```json
[
  {
    "scanner_name": "pii_detection",
    "enabled": true,
    "sensitivity": "medium"
  },
  {
    "scanner_name": "prompt_injection",
    "enabled": true,
    "sensitivity": "medium"
  },
  {
    "scanner_name": "jailbreak",
    "enabled": true,
    "sensitivity": "medium"
  },
  {
    "scanner_name": "toxicity",
    "enabled": true,
    "sensitivity": "medium"
  },
  {
    "scanner_name": "ban_topics",
    "enabled": true,
    "sensitivity": "medium"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `scanner_name` | `string` | Scanner identifier (unique) |
| `enabled` | `bool` | Whether scanner is active |
| `sensitivity` | `string` | `"low"`, `"medium"`, or `"high"` |

Default scanner names (seeded on first access): `pii_detection`, `prompt_injection`, `jailbreak`, `toxicity`, `ban_topics`.

#### `PUT /api/admin/policy/{scanner_name}`

Update a scanner policy configuration.

**Path Parameters**:

| Name | Type | Description |
|------|------|-------------|
| `scanner_name` | `string` | Exact scanner name to update |

**Request Body** (`UpdatePolicyRequest`):

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `enabled` | `bool` | Yes | — | Whether scanner is active |
| `sensitivity` | `string` | Yes | `"low" \| "medium" \| "high"` | Detection sensitivity level |

**Request Example**:

```json
{
  "enabled": true,
  "sensitivity": "high"
}
```

**Success Response** `200 OK`:

Returns `PolicyConfigResponse`.

**Error Response** `404 Not Found`:

```json
{
  "detail": "Scanner not found"
}
```

---

## Error Responses

All error responses follow a consistent JSON format:

```json
{
  "detail": "Human-readable error message"
}
```

### Standard Error Codes

| HTTP Status | Condition | Typical `detail` Values |
|-------------|-----------|------------------------|
| `400 Bad Request` | Invalid input, model not found | `"Invalid role: X. Must be 'employee' or 'admin'."`, `"Model 'X' not available"` |
| `401 Unauthorized` | Missing/invalid/expired session | `"Not authenticated"`, `"Invalid session"`, `"Session expired"`, `"User not found"`, `"Invalid state token"`, `"State token expired"` |
| `403 Forbidden` | Non-admin accessing admin endpoint; user accessing another user's conversation | `"Admin access required"`, `"Access denied"` |
| `404 Not Found` | Model config or policy not found | `"Model not found"`, `"Scanner not found"` |
| `500 Internal Server Error` | Unexpected server errors | FastAPI default error format |

### 401 Response Format

```json
{
  "detail": "Not authenticated"
}
```

The `401` response never includes user identity or role information (per security requirements T-01-02, T-01-10).

### 403 Response Format

```json
{
  "detail": "Admin access required"
}
```

The `403` response contains only a generic message — no role enumeration or user identity hints (per T-01-10).

---

## Risk Categories

The safety pipeline uses these risk categories across all scanners:

| Category | Description | Scanner Source |
|----------|-------------|---------------|
| `pii` | Personal Identifiable Information | `DataProtectionScanner` (Presidio) |
| `sensitive_data` | Corporate sensitive data | `DataProtectionScanner` (Presidio) |
| `prompt_injection` | Prompt injection attempts | `LLMGuardrailScanner` (LLM Guard) |
| `jailbreak` | Jailbreak/bypass attempts | `LLMGuardrailScanner` (LLM Guard) |
| `harmful_content` | Toxic, harmful, or inappropriate content | `LLMGuardrailScanner` (LLM Guard) |
| `compliance` | Compliance policy violations | `LLMGuardrailScanner` (LLM Guard) |

## Block Message Templates

Block messages are category-specific and never echo detected content. Templates are defined in `BLOCK_MESSAGE_TEMPLATES` with separate wording for input vs. output. When multiple categories are detected, the highest-severity category template is used (severity order: jailbreak > prompt_injection > harmful_content > pii > sensitive_data > compliance).

The fail-closed fallback message is: `"系统处理异常，请稍后重试。"`

## Message Roles in Conversation Storage

| Role | Description |
|------|-------------|
| `user` | User's original message |
| `assistant` | Model's allowed response |
| `blocked` | Block notice (never raw content) — stored with `extra: {"risk_categories": [...]}` |
| `system` | System messages (VERIFY: not currently created by API endpoints) |
| `tool` | Tool call results (VERIFY: not currently created by API endpoints) |

When building model call history, `blocked` messages are excluded entirely. Unknown roles are mapped to `user` for the model API call.

---

## SSE Client Connection Notes

- The SSE stream uses the `sse-starlette` library on the server side. Clients should use `EventSource` API or `eventsource-parser` to consume the stream.
- Each SSE event has an `event` field (type name) and a `data` field (JSON-encoded string).
- The stream ends after a `done`, `blocked`, or `error` event. No explicit close event is sent beyond these terminal events.
- Client disconnection is handled gracefully: the server shields DB cleanup with `asyncio.shield` to prevent session leaks on cancel.