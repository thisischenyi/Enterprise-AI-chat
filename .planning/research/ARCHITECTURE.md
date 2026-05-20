# Architecture Patterns

**Domain:** Enterprise AI chat with safety filtering
**Researched:** 2026-05-21

## Recommended Architecture

The system uses a **backend-gated pipeline architecture** where the backend is the sole enforcement point for all safety and model interaction policies. The frontend never contacts model providers directly. All user input flows through a safety pipeline before reaching any LLM, and all model output flows through a safety pipeline before reaching the user.

```
                    +------------------+
                    |  Enterprise IDP  |
                    |  (OIDC Provider) |
                    +--------+---------+
                             |
                             | OIDC tokens
                             v
+----------+    +------------+-----------+    +-------------------+
| React    |    |     FastAPI Backend     |    |   PostgreSQL      |
| Frontend |<-->|                         |<-->|   Database        |
| (Chat +  |    |  Auth Middleware        |    |                   |
|  Admin)  |    |  Safety Pipeline        |    |  - conversations  |
+----------+    |  Model Gateway          |    |  - audit_events   |
                |  Admin API              |    |  - model_configs  |
                +------------+-----------+    |  - policies       |
                             |                +-------------------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
   +----------+--------+      +------------+----------+
   | Presidio Scanner   |      | LLM Guardrail Scanner |
   | (DataProtection)   |      | (Llama Guard /        |
   | - PII detection    |      |  LLM Guard)           |
   | - Data classification|    | - Jailbreak detection |
   +----------+--------+      | - Prompt injection    |
              |                | - Harmful content     |
              |                | - Compliance checks   |
              +--------+-------+---------+
                       |                 |
                       v                 v
           +-----------+-----------+    +-----------+-----------+
           | Alibaba Bailian Qwen  |    | Local OpenAI-Compatible|
           | (Cloud LLM Provider)  |    | (Self-Hosted Provider) |
           +-----------------------+    +------------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **React Frontend** | Chat UI, admin dashboard, auth-triggered login flow | FastAPI Backend (REST + SSE) |
| **Auth Middleware** | OIDC token validation, role extraction (employee/admin), request gating | Frontend (provides JWT), all backend routes (enforces access) |
| **Safety Pipeline (Input)** | Scans user messages for PII, sensitive data classification, prompt injection, jailbreak attempts before model calls | Frontend (receives input), DataProtectionScanner, LLMGuardrailScanner (delegates scanning) |
| **Safety Pipeline (Output)** | Scans model responses for harmful content, compliance violations, leaked PII before display | Model Gateway (receives raw output), DataProtectionScanner, LLMGuardrailScanner (delegates scanning) |
| **DataProtectionScanner** | Presidio-based PII detection and data classification; wraps Presidio behind an internal interface | Safety Pipeline (called by), Presidio library (calls) |
| **LLMGuardrailScanner** | Llama Guard / LLM Guard-based jailbreak, injection, harmful content, compliance detection; wraps behind internal interface | Safety Pipeline (called by), Llama Guard / LLM Guard library (calls) |
| **Model Gateway** | Routes chat requests to configured provider (Qwen or local OpenAI-compatible); handles streaming response ingestion | Safety Pipeline Output (provides raw model output), configured LLM providers (API calls) |
| **Conversation Store** | Persists only allowed-through conversation content; never stores blocked content raw text | Safety Pipeline (stores only after output safety pass), Frontend (serves conversation history) |
| **Audit Logger** | Creates audit events with metadata and risk categories; never stores raw sensitive content | Safety Pipeline (receives audit events for both allow and block decisions), Admin Dashboard (serves audit viewer) |
| **Admin API** | CRUD for model provider configs, policy thresholds, scanner module toggles; restricted to admin role | Auth Middleware (role-gated), Frontend Admin Dashboard, PostgreSQL (reads/writes configs) |
| **Enterprise IDP** | OIDC authentication provider; MVP uses mock OIDC, real IDP adapter swapped later | Auth Middleware (provides tokens), Frontend (login redirect) |
| **PostgreSQL** | Persistence for conversations, audit events, model configs, policy configs | All backend components (via ORM/data access layer) |

### Data Flow

**1. Successful Chat Flow (Allowed Content):**

```
User types message
  -> Frontend sends POST /api/chat (with JWT)
  -> Auth Middleware validates OIDC token, extracts role
  -> Input Safety Pipeline receives user message
     -> DataProtectionScanner: scans for PII and data classification
     -> LLMGuardrailScanner: scans for injection/jailbreak/harmful content
     -> Both scanners return PASS (no violations)
  -> Safety Pipeline logs ALLOW audit event (metadata only)
  -> Model Gateway receives clean message, routes to selected provider
  -> Provider streams response chunks back to Model Gateway
  -> Output Safety Pipeline receives each chunk via safety buffer
     -> DataProtectionScanner: scans for PII leakage in response
     -> LLMGuardrailScanner: scans for harmful/compliant response content
     -> Buffer accumulates chunks, checks at configured intervals
     -> All chunks pass safety checks
  -> Streamed safe content forwarded to Frontend via SSE
  -> Conversation Store saves only allowed-through content
  -> Frontend displays streamed response to user
```

**2. Blocked Input Flow:**

```
User types message
  -> Frontend sends POST /api/chat (with JWT)
  -> Auth Middleware validates OIDC token
  -> Input Safety Pipeline receives user message
     -> Scanner(s) detect violation (e.g., PII detected, jailbreak attempt)
     -> Violation includes: risk category, confidence score, scanner module name
  -> Safety Pipeline BLOCKS: does NOT forward to Model Gateway
  -> Safety Pipeline logs BLOCK audit event (metadata + risk categories, NO raw content)
  -> Safety Pipeline returns safe block message to Frontend:
     "Your message was blocked because it contained [risk category].
      [Action taken]. Please revise your message."
  -> Frontend displays block explanation to user
  -> NO model call made. NO sensitive content stored.
```

**3. Blocked Output Flow:**

```
Model streams response chunks
  -> Model Gateway accumulates in safety buffer
  -> Output Safety Pipeline checks buffered chunks
     -> Scanner(s) detect violation in model output
  -> Safety Pipeline BLOCKS: stops streaming to frontend
  -> Safety Pipeline logs BLOCK audit event (metadata, NO raw model output)
  -> Safety Pipeline returns safe block message:
     "The model response was blocked because it contained [risk category].
      [Action taken]."
  -> Frontend displays output block explanation
  -> NO unsafe model content reaches frontend. NO unsafe content stored.
  -> Conversation Store saves only the safe block explanation message
```

**4. Admin Configuration Flow:**

```
Admin opens dashboard
  -> Frontend sends GET /api/admin/configs (with admin-role JWT)
  -> Auth Middleware validates token AND checks admin role
  -> Admin API serves model configs, policy thresholds, scanner toggles
  -> Admin modifies configuration
  -> Frontend sends PUT /api/admin/configs
  -> Auth Middleware validates + admin role check
  -> Admin API validates and persists changes to PostgreSQL
  -> Changes propagate to Safety Pipeline and Model Gateway at next request
```

**5. Conversation History Flow:**

```
User requests conversation list
  -> Frontend sends GET /api/conversations (with JWT)
  -> Auth Middleware validates employee role
  -> Conversation Store returns list (only contains allowed-through content)
  -> User selects conversation to resume
  -> Frontend sends GET /api/conversations/{id}/messages
  -> Conversation Store returns message history (safe content only)
  -> User continues chat in existing conversation context
```

## Streaming Safety Buffer Pattern

This is the most architecturally significant pattern in the system. Naive streaming sends model output directly to users for responsiveness, but safety checks cannot run on incomplete content. The safety buffer reconciles these competing demands.

**Pattern: Chunked Safety Buffer**

```
Model produces chunk 1, 2, 3, ... (streaming)
  -> Buffer accumulates chunks until:
     (a) Buffer reaches configured size threshold (e.g., N tokens)
     (b) Buffer reaches configured time threshold (e.g., T milliseconds)
     (c) Stream ends (final chunk)
  -> Safety Pipeline scans buffered content
  -> If PASS: buffered content flushed to frontend via SSE
  -> If BLOCK: stream interrupted, block message sent, buffered unsafe content discarded
  -> Repeat for next buffer fill
```

**Key configuration parameters:**
- Buffer size threshold: smaller = faster display, more frequent scans, slightly higher overhead
- Buffer time threshold: prevents indefinite buffering on slow model responses
- Scanner timeout: maximum time allowed for safety scan per buffer batch
- End-of-stream flush: always scan final partial buffer before closing SSE connection

**Why this matters for build order:** The streaming buffer must be designed and tested before the output safety pipeline can be integrated. Without the buffer mechanism, you either stream unsafe content or block entirely until the full response is available (which eliminates the streaming UX benefit).

## Patterns to Follow

### Pattern 1: Scanner Interface Abstraction
**What:** All safety scanners implement a common internal interface (`ScannerProtocol` or equivalent), regardless of underlying library. DataProtectionScanner wraps Presidio; LLMGuardrailScanner wraps Llama Guard / LLM Guard. Each scanner returns a standardized result: `{passed: bool, risk_categories: list, confidence: float, scanner_name: str}`.
**When:** Any time you add, replace, or configure a safety scanner.
**Why:** The project explicitly requires scanners to be swappable. Without a common interface, swapping Presidio for a different PII library or Llama Guard for a different guardrail model requires changing the Safety Pipeline internals. With the interface, you only implement a new scanner adapter.
**Example:**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class ScanResult:
    passed: bool
    risk_categories: List[str]
    confidence: float
    scanner_name: str

class Scanner(ABC):
    @abstractmethod
    def scan(self, content: str, context: dict) -> ScanResult:
        """Scan content and return standardized result."""
        pass

class DataProtectionScanner(Scanner):
    """Wraps Presidio for PII and data classification."""
    def scan(self, content: str, context: dict) -> ScanResult:
        # Presidio-specific implementation
        analyzer_results = self.analyzer.analyze(content, language=context.get("language", "en"))
        if analyzer_results:
            return ScanResult(
                passed=False,
                risk_categories=["PII_DETECTED"],
                confidence=max(r.score for r in analyzer_results),
                scanner_name="DataProtectionScanner"
            )
        return ScanResult(passed=True, risk_categories=[], confidence=1.0, scanner_name="DataProtectionScanner")

class LLMGuardrailScanner(Scanner):
    """Wraps Llama Guard / LLM Guard for jailbreak, injection, harmful content."""
    def scan(self, content: str, context: dict) -> ScanResult:
        # Llama Guard / LLM Guard specific implementation
        ...
```

### Pattern 2: Backend-Only Safety Enforcement
**What:** The frontend never calls model providers directly. All safety checks run on the backend. The frontend receives only pre-scanned content or block messages.
**When:** Always. This is a hard constraint from the project requirements.
**Why:** If the frontend can bypass safety checks (e.g., by calling a model API directly), the entire safety pipeline is useless. Enterprise safety must be enforced at a single, controlled gateway.
**Example:**
```python
# Backend route enforces safety before any model call
@router.post("/api/chat")
async def chat(request: ChatRequest, user: User = Depends(get_current_user)):
    # 1. Input safety scan (MANDATORY before model call)
    input_result = await safety_pipeline.scan_input(request.message, context={"user": user})
    if not input_result.passed:
        await audit_logger.log_block(input_result, user)
        return ChatBlockResponse(
            message=f"Blocked: {input_result.risk_categories}",
            action="INPUT_BLOCKED"
        )
    # 2. Only proceed to model if input passes
    model_response = await model_gateway.call_model(request.model, request.message)
    # 3. Output safety scan (MANDATORY before display)
    output_result = await safety_pipeline.scan_output(model_response, context={"user": user})
    if not output_result.passed:
        await audit_logger.log_block(output_result, user)
        return ChatBlockResponse(
            message=f"Blocked: {output_result.risk_categories}",
            action="OUTPUT_BLOCKED"
        )
    # 4. Only store and return if output passes
    await conversation_store.save_message(conversation_id, user_message, model_response)
    await audit_logger.log_allow(input_result, output_result, user)
    return ChatSuccessResponse(content=model_response)
```

### Pattern 3: Audit Metadata Only (No Raw Content Storage)
**What:** Audit events store risk categories, scanner names, confidence scores, timestamps, and user identifiers, but never store the raw user message or raw model output that triggered a block.
**When:** Any audit logging operation.
**Why:** Storing the sensitive content you are trying to protect creates a new data protection problem. The database must not become a vault of the content the safety pipeline is designed to block.
**Example:**
```python
@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    user_id: str  # from OIDC token
    action: str   # "ALLOW" or "BLOCK"
    direction: str  # "INPUT" or "OUTPUT"
    risk_categories: List[str]  # e.g., ["PII_DETECTED", "JAILBREAK"]
    scanner_names: List[str]   # e.g., ["DataProtectionScanner"]
    confidence_scores: List[float]
    model_provider: str  # e.g., "qwen" or "local-openai"
    conversation_id: str
    # NOTE: NO raw_content field. NO raw model output field.
```

### Pattern 4: Policy-Driven Safety Configuration
**What:** Admin-configurable policy thresholds and scanner toggles control what the safety pipeline checks and at what sensitivity. Policies are stored in PostgreSQL and read by the safety pipeline at runtime.
**When:** Safety pipeline initialization and per-request policy lookups.
**Why:** Different enterprises have different sensitivity thresholds. A financial services company may block on low-confidence PII detection, while a tech company may only block on high-confidence. Hardcoded thresholds require code changes for policy adjustments.
**Example:**
```python
@dataclass
class SafetyPolicy:
    policy_id: str
    enabled_scanners: List[str]  # which scanners to run
    thresholds: Dict[str, float]  # e.g., {"PII_DETECTED": 0.7, "JAILBREAK": 0.5}
    block_action: str  # what to do on block (always "BLOCK_FULL" for MVP)

class SafetyPipeline:
    def __init__(self, scanners: List[Scanner], policy_repo: PolicyRepository):
        self.scanners = scanners
        self.policy_repo = policy_repo

    async def scan_input(self, content: str, context: dict) -> PipelineResult:
        policy = await self.policy_repo.get_active_policy()
        results = []
        for scanner in self.scanners:
            if scanner.scanner_name in policy.enabled_scanners:
                result = scanner.scan(content, context)
                if not result.passed and result.confidence >= policy.thresholds.get(result.risk_categories[0], 0.5):
                    return PipelineResult(passed=False, block_reason=result)
                results.append(result)
        return PipelineResult(passed=True, scan_results=results)
```

### Pattern 5: SSE Streaming with Safety Buffer
**What:** Server-Sent Events (SSE) stream model output to the frontend, but a safety buffer intercepts chunks before they are sent. The buffer accumulates chunks until a threshold is reached, then runs safety scans on the accumulated content. Safe content is flushed; unsafe content triggers a stream interrupt and block message.
**When:** All streaming chat responses.
**Why:** Users expect responsive streaming output. But safety checks on individual tiny tokens are unreliable (a harmful word may be split across chunks). Buffering solves both: responsiveness (stream in bursts) and safety (scan meaningful content segments).
**Example:**
```python
async def stream_chat(request: ChatRequest, user: User):
    # Input safety check first (non-streaming, full message available)
    input_result = await safety_pipeline.scan_input(request.message, context={"user": user})
    if not input_result.passed:
        yield SSEEvent(event="block", data=json.dumps({"message": "...", "action": "INPUT_BLOCKED"}))
        return

    # Stream model output with safety buffer
    buffer = SafetyBuffer(size_threshold=50, time_threshold_ms=500)
    model_stream = model_gateway.stream_model(request.model, request.message)

    for chunk in model_stream:
        buffer.add(chunk)
        if buffer.is_ready_to_scan():
            buffered_content = buffer.flush()
            output_result = await safety_pipeline.scan_output(buffered_content, context={"user": user})
            if not output_result.passed:
                yield SSEEvent(event="block", data=json.dumps({"message": "...", "action": "OUTPUT_BLOCKED"}))
                buffer.clear()
                return  # stop stream
            yield SSEEvent(event="content", data=json.dumps({"content": buffered_content}))

    # Flush remaining buffer at stream end
    if buffer.has_content():
        final_content = buffer.flush()
        final_result = await safety_pipeline.scan_output(final_content, context={"user": user})
        if final_result.passed:
            yield SSEEvent(event="content", data=json.dumps({"content": final_content}))
        else:
            yield SSEEvent(event="block", data=json.dumps({"message": "...", "action": "OUTPUT_BLOCKED"}))

    yield SSEEvent(event="done", data="")
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Frontend Direct Model Access
**What:** Allowing the frontend to call model provider APIs directly (bypassing backend safety).
**Why bad:** Completely defeats the safety pipeline. A browser extension or API call could send unrestricted content to models and receive unchecked responses.
**Instead:** All model calls go through the backend Model Gateway. Frontend only communicates with the backend via `/api/chat` SSE endpoint.

### Anti-Pattern 2: Storing Blocked Content in Database
**What:** Saving the raw user message or raw model output that was blocked into the database for "debugging" or "analysis."
**Why bad:** The database becomes a store of the sensitive content the system is designed to protect. This creates a data protection violation and potential compliance breach.
**Instead:** Audit events store only metadata: risk categories, confidence scores, scanner names, timestamps. No raw content. If debugging is needed, use ephemeral logs with access controls, not persistent database storage.

### Anti-Pattern 3: Per-Token Safety Checks During Streaming
**What:** Running safety scans on every individual streaming token/chunk as it arrives.
**Why bad:** Individual tokens are too small for reliable PII or harmful content detection. "Social Security Number 123-45-6789" split across 10 tokens cannot be detected token-by-token. Per-token scanning also adds unacceptable latency to every streaming chunk.
**Instead:** Use a safety buffer that accumulates meaningful content segments (configured by size and time thresholds) and scans those segments. This balances responsiveness with detection accuracy.

### Anti-Pattern 4: Hardcoded Safety Thresholds
**What:** Embedding confidence thresholds and enabled scanner lists directly in code as constants.
**Why bad:** Changing a threshold (e.g., from 0.7 to 0.5 for PII detection) requires a code change and redeployment. Different enterprises need different sensitivity levels.
**Instead:** Store policies in PostgreSQL with admin CRUD API. Safety pipeline reads active policy per request. Thresholds and scanner toggles change without code deployment.

### Anti-Pattern 5: Single Scanner for All Checks
**What:** Using one scanner (e.g., only Llama Guard) for both PII detection and harmful content detection.
**Why bad:** PII detection requires different techniques than jailbreak detection. Presidio is purpose-built for structured PII (names, SSNs, emails) with regex + NLP models. Llama Guard is purpose-built for harmful content and prompt attacks. Using only one means either poor PII detection or poor harmful content detection.
**Instead:** Separate scanners with separate interfaces: DataProtectionScanner (Presidio) for PII/data classification, LLMGuardrailScanner (Llama Guard / LLM Guard) for jailbreak/injection/harmful content. Safety Pipeline orchestrates both.

### Anti-Pattern 6: Synchronous Blocking on Streaming Output
**What:** Waiting for the complete model response before running any safety checks (i.e., not streaming until the entire response is available and verified).
**Why bad:** Users stare at an empty screen for potentially 10-30 seconds while waiting for a long model response. This feels like a broken system, not a responsive chat.
**Instead:** Safety buffer pattern: stream content in bursts after each buffer pass. User sees content appear in segments (similar to how ChatGPT streams), while safety checks verify each segment before it is sent.

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| Safety scan latency | Single-process, scanners in-memory | Separate scanner worker processes or async scanning | Dedicated scanner service with horizontal scaling |
| Model API throughput | Direct API calls, no queue | Request queuing with rate limiting | Multiple model provider replicas, load balancing |
| SSE connection management | uvicorn handles natively | Connection pool management, timeout policies | Dedicated SSE gateway (e.g., reverse proxy with SSE support) |
| Database queries | Single PostgreSQL instance sufficient | Read replicas for conversation history, write primary for events | Sharded conversations, time-partitioned audit events |
| Audit event volume | Store all events in single table | Partitioned tables by date, periodic archival | Event streaming to separate analytics store (e.g., ClickHouse) |
| Safety buffer memory | Per-request buffer, negligible | Buffer pool with size limits, per-user connection limits | Distributed buffer management, backpressure on model streams |

**MVP scaling target:** 100 internal users, single PostgreSQL instance, single uvicorn process, in-memory scanners. This is the correct starting point. Do not over-engineer scaling for the MVP demo.

## Suggested Build Order (Component Dependencies)

The build order is determined by dependency chains. Components must be built in an order where each new component has everything it needs to function.

```
Phase 1: Foundation (no dependencies)
  [1a] PostgreSQL schema: conversations, audit_events, model_configs, policies tables
  [1b] FastAPI project skeleton: route structure, dependency injection setup
  [1c] Auth middleware: OIDC token validation (mock OIDC first)
  [1d] React frontend skeleton: routing, layout, auth-triggered login

Phase 2: Safety Core (depends on Phase 1)
  [2a] Scanner interface abstraction: Scanner ABC, ScanResult dataclass
  [2b] DataProtectionScanner: Presidio integration, PII detection
  [2c] LLMGuardrailScanner: Llama Guard / LLM Guard integration
  [2d] Safety Pipeline: orchestrates scanners, returns pass/block results
  [2e] Safety Buffer: chunked buffer for streaming output scanning
  [2f] Audit Logger: creates metadata-only audit events on pass/block

Phase 3: Model Integration (depends on Phase 2 safety pipeline)
  [3a] Model Gateway: provider abstraction, routes to Qwen / local OpenAI-compatible
  [3b] Streaming response ingestion: SSE from model providers to buffer
  [3c] Chat API: end-to-end input safety -> model call -> output safety -> SSE to frontend
  [3d] Conversation Store: persist only allowed-through content

Phase 4: User Experience (depends on Phase 3)
  [4a] Chat UI: message input, streamed response display, block message display
  [4b] Conversation history UI: browse and resume past conversations
  [4c] SSE client integration: receive streaming content and block events

Phase 5: Admin Controls (depends on Phase 2 safety pipeline + Phase 1 schema)
  [5a] Admin API: CRUD for model configs, policy thresholds, scanner toggles
  [5b] Admin Dashboard UI: model config, policy config, scanner toggle screens
  [5c] Audit viewer UI: filter and view audit event metadata

Phase 6: Testing and Hardening (depends on all above)
  [6a] Automated tests: allow path, input block path, output block path, streaming buffer
  [6b] Policy configuration tests: threshold changes affect safety decisions
  [6c] Integration tests: end-to-end OIDC -> chat -> safety -> model -> display
```

**Build order rationale:**
- Safety pipeline MUST exist before model calls are made. Without safety, you have an unsafe chat system, not the product you are building.
- Scanner interfaces come before scanner implementations so the safety pipeline can be built against the interface, not a specific library.
- Safety buffer MUST be designed before streaming output can be implemented. Without the buffer, streaming output bypasses safety.
- Auth middleware comes first because every other endpoint depends on authenticated requests.
- Admin controls can be built in parallel with chat UX once the safety pipeline exists, but chat UX is the primary demo path.
- Testing comes last because it validates the complete system, but unit tests for individual components should be written alongside each component.

## Sources

- PROJECT.md: Project requirements and constraints (primary source for component boundaries)
- Microsoft Presidio documentation: PII detection architecture patterns (MEDIUM confidence - training data, needs verification against current docs)
- Llama Guard documentation: guardrail scanning patterns (MEDIUM confidence - training data, needs verification)
- FastAPI documentation: SSE streaming patterns (MEDIUM confidence - training data)
- Enterprise AI chat architecture patterns: backend-gated pipeline approach (MEDIUM confidence - industry pattern, widely used)