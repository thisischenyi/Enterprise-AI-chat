# Domain Pitfalls

**Domain:** Enterprise AI chat with safety filtering (Presidio + Llama Guard / LLM Guard)
**Researched:** 2026-05-21
**Confidence:** MEDIUM (based on domain expertise; WebSearch/Bash/Context7 unavailable for verification)

## Critical Pitfalls

Mistakes that cause rewrites, data leaks, or safety failures.

### Pitfall 1: Streaming Buffer Bypass (Unsafe Content Reaches User Before Block)

**What goes wrong:** During streaming response, tokens are sent to the frontend before the safety scanner finishes evaluating them. If the scanner flags content as unsafe after the frontend has already rendered some tokens, the user sees sensitive or harmful content that should have been blocked. This is the single most dangerous pitfall in this project — it directly violates the core value proposition ("block unsafe content before display").

**Why it happens:** Streaming and safety scanning have inherently different speeds. Llama Guard / LLM Guard inference takes 50-200ms per evaluation window, while SSE tokens can arrive every 10-30ms. Teams often start streaming immediately and run safety checks asynchronously, assuming they can retroactively suppress flagged content. But once the browser renders text, retroactive deletion is unreliable (DOM mutations are visible in DevTools, screen captures happen before deletion, accessibility tools may cache the text).

**Consequences:** Sensitive PII or harmful content briefly visible to the employee. Screen capture, browser DevTools, or accessibility readers can capture the transient content. Safety guarantee is broken at the fundamental level.

**Prevention:**
- Implement a strict buffer window: accumulate N tokens (or M characters) on the backend before flushing to SSE. The buffer size must be at least the maximum scanner evaluation chunk size. Only flush tokens that have been cleared by the output scanner.
- Never stream "pending" tokens. The frontend should only receive tokens that have an explicit `ALLOW` verdict.
- If the scanner flags content mid-stream, immediately send a `BLOCK` SSE event and terminate the stream. Do NOT attempt to retroactively delete previously sent tokens — they are already in the client.
- Test this explicitly: write automated tests that send prompts known to produce unsafe output mid-stream and verify that no unsafe token reaches the frontend SSE payload.

**Detection:** Write a test harness that logs every SSE chunk received by a mock frontend client. Verify that no chunk contains content that would be flagged by the safety scanner. If any flagged content appears in SSE logs, the buffer is leaking.

**Phase:** Phase 2 (Safety Pipeline Implementation) — this is the core pipeline mechanics and must be designed correctly from the start. Retrofitting a buffer-after-scan architecture onto a stream-then-scan system requires a rewrite of the entire streaming layer.

---

### Pitfall 2: Echoing Blocked Content in Error Messages (PII Leak Through Block Message)

**What goes wrong:** When input or output is blocked, the explanation message to the user inadvertently includes the sensitive content itself. Example: "Your message was blocked because it contains SSN 123-45-6789" or "The model response was blocked for containing the phone number 555-1234." The block message becomes a PII leak vector.

**Why it happens:** The scanner detects PII and returns the detected entities along with the verdict. Developers naturally want informative error messages and include the detected entity text for debugging clarity. This is especially tempting during development when detailed messages help testing.

**Consequences:** The user receives a message that contains the exact PII that was supposed to be blocked. This violates the project requirement ("Block messages explain the risk category and action taken without echoing sensitive content") and creates a compliance risk — the block notification itself contains sensitive data.

**Prevention:**
- The `PolicyDecision` / block message must NEVER include the raw detected entity text. Only include: (1) the risk category (e.g., "PII_DETECTED", "HARMFUL_CONTENT"), (2) the entity type (e.g., "SSN", "PHONE_NUMBER"), and (3) the action taken ("BLOCKED").
- Presidio returns `RecognizerResult` with entity type and position but does NOT need to carry the raw text into the policy decision. Strip entity text at the scanner interface boundary — `DataProtectionScanner.analyze()` should return a list of `{entity_type, risk_category, confidence}` without the matched substring.
- Enforce this with a dedicated test: every blocked message must pass a "no echoed PII" check that runs Presidio on the block message itself. If Presidio detects PII in the block explanation, the message is itself a leak.
- In development, use a debug mode that logs entity details server-side only (not sent to frontend). Production mode must use sanitized messages.

**Detection:** Automated test: after generating a block message, run Presidio on the message text. If any PII entity is detected in the block message itself, fail the test.

**Phase:** Phase 2 (Safety Pipeline Implementation) — the `PolicyDecision` and block message format must be designed from day one to exclude raw entity text.

---

### Pitfall 3: False Negatives in PII Detection (Presidio Misses Enterprise-Specific PII)

**What goes wrong:** Presidio's default recognizers detect common US PII (SSN, email, phone number, credit card) but miss enterprise-specific sensitive data: employee IDs, project codes, internal system names, classification labels ("CONFIDENTIAL-PROJECT-X"), proprietary identifiers, and non-US PII formats (Chinese national ID numbers, Chinese phone numbers, internal enterprise identifiers used with Qwen). Content passes the scanner and is stored in the database or displayed to the user, creating a compliance violation.

**Why it happens:** Presidio ships with recognizers optimized for common US/Western PII patterns. Enterprise environments have domain-specific sensitive data types that do not match any default recognizer pattern. Teams deploy Presidio with defaults, see it catching emails and phone numbers, and assume it is "working." They do not invest in custom recognizers for their specific data types.

**Consequences:** Enterprise-specific sensitive data leaks through the safety pipeline. Database stores content containing internal identifiers. Employees see classified project references that should have been blocked. Compliance audit finds data that should have been caught but was not.

**Prevention:**
- Before deploying Presidio, inventory all enterprise-specific sensitive data types that must be detected: employee IDs, project codes, system identifiers, classification labels, Chinese PII formats (national ID, phone, address), proprietary data patterns.
- Implement custom Presidio recognizers for each enterprise-specific data type. Presidio supports regex-based, pattern-based, and ML-based custom recognizers. Start with regex recognizers for structured identifiers (employee IDs follow a known pattern) and add NLP-based recognizers for unstructured references.
- Specifically add recognizers for Chinese PII formats since the project integrates Qwen (Chinese LLM). Chinese national ID (18-digit), Chinese phone numbers (11-digit starting with 1), and Chinese addresses have distinct patterns that Presidio defaults do not cover.
- Tune confidence thresholds per recognizer type. Default thresholds are often too low for enterprise use — a 0.5 confidence match on "PHONE_NUMBER" catches too many false positives on numeric strings that are not phone numbers.

**Detection:** Run Presidio on a curated test corpus of enterprise-specific sensitive data examples. If any example is not detected, a custom recognizer is needed. Repeat this test periodically as new data types are identified.

**Phase:** Phase 3 (Policy Configuration and Tuning) — custom recognizers are configured alongside policy thresholds. But the recognizer inventory must start in Phase 2 so that the `DataProtectionScanner` interface is designed to support custom recognizers from the beginning.

---

### Pitfall 4: Audit Metadata Reconstructing Sensitive Content

**What goes wrong:** Audit events are designed to contain "metadata and risk categories but not raw sensitive content." However, metadata fields can be more revealing than intended. If audit records contain the entity type ("SSN"), the position in the original text (character offset), the confidence score, and the surrounding context category, an analyst with access to the audit table can reconstruct the original sensitive content through inference, pattern matching, or correlation with other data sources.

**Why it happens:** Developers want rich audit metadata for debugging and compliance reporting. They log entity types, positions, confidence scores, scanner names, and sometimes the "context window" around the detected entity (surrounding N characters). Each piece seems harmless individually, but together they can reconstruct the blocked content.

**Consequences:** The audit database becomes a secondary store of sensitive information, violating the same compliance requirements that the safety pipeline was designed to enforce. Compliance auditors flag the audit table as a data leak risk.

**Prevention:**
- Define a strict audit schema that contains ONLY: (1) event timestamp, (2) user ID, (3) conversation ID (if applicable), (4) direction (input/output), (5) risk categories detected (list of category labels, no entity text), (6) action taken (ALLOW/BLOCK), (7) scanner IDs that triggered the block, (8) model provider and model name, (9) confidence level range (e.g., "high" not the exact 0.87 score).
- NEVER log: raw entity text, character offsets into original content, context windows, partial content excerpts, or exact confidence scores (round to coarse buckets).
- Review the audit schema with a security/compliance perspective: "If I had access to this table and the user's conversation history (which contains only allowed-through content), could I reconstruct what was blocked?" If yes, remove the revealing field.
- Encrypt or hash user IDs in audit records if the audit table is accessible to broader teams than the security team.

**Detection:** Periodic audit review: examine audit records and attempt inference attacks. Can you determine the specific SSN value from the metadata? Can you narrow down the blocked content to a specific phrase? If yes, the schema is too rich.

**Phase:** Phase 2 (Safety Pipeline Implementation) — the audit event schema must be designed alongside the safety pipeline. Retrofitting audit fields to remove sensitive metadata is a database migration that is risky and disruptive.

---

### Pitfall 5: Scanner Failure Defaulting to Allow (Content Passes Unfiltered When Scanner Crashes)

**What goes wrong:** When Presidio, Llama Guard, or LLM Guard throws an exception, times out, or returns an unexpected error, the safety pipeline catches the exception and... allows the content to pass through. The rationale is "fail open so the user experience is not degraded." But failing open means that the safety guarantee is void whenever the scanner is unavailable, which defeats the entire purpose of the system.

**Why it happens:** Developers wrap scanner calls in try/except blocks. The catch path returns `PolicyAction.ALLOW` because blocking everything when a scanner is down seems like a bad user experience. This decision is often made casually during development without considering the security implications.

**Consequences:** Any scanner downtime, crash, or timeout creates a window where all content passes unfiltered. This is the worst-case scenario for an enterprise safety system — the safety mechanism is off precisely when it might be needed most (if a scanner crash was triggered by a malformed adversarial input).

**Prevention:**
- Default to `PolicyAction.BLOCK` on scanner failure. The policy should be: "If we cannot verify safety, we do not allow the content." This is the same principle as a firewall — if the firewall cannot evaluate the packet, it drops it.
- Differentiate scanner failure types:
  - Scanner timeout → BLOCK with message "Safety check could not complete. Please retry."
  - Scanner crash/exception → BLOCK with message "Safety system error. Content cannot be processed."
  - Scanner returns invalid/unexpected format → BLOCK (invalid verdict = no verdict = cannot verify safety).
- Log all scanner failures as high-priority audit events (the failure itself is an operational security event).
- Implement retry with exponential backoff for timeout scenarios, but still BLOCK on the first attempt. Let the user retry manually.
- In the admin dashboard, surface scanner failure rates prominently. High failure rates indicate infrastructure problems that need immediate attention.

**Detection:** Monitor scanner failure audit events. If the failure rate exceeds a threshold (e.g., 1% of requests), trigger an alert. Also test: deliberately make a scanner unavailable and verify that all requests are blocked, not allowed through.

**Phase:** Phase 2 (Safety Pipeline Implementation) — the `PolicyEngine` must be designed with fail-closed semantics from the start. Changing from fail-open to fail-closed after launch changes the security posture fundamentally and requires re-testing all flows.

---

### Pitfall 6: Safety Scanner Running on Partial/Truncated Content

**What goes wrong:** The output safety scanner receives incomplete chunks of the model's streaming response (a partial sentence, a truncated paragraph) and evaluates them. PII detection and harmful content classification on incomplete text produces significantly worse results — Presidio cannot reliably detect an SSN that spans a chunk boundary, and Llama Guard cannot reliably classify harmful intent from a partial sentence that is cut off mid-thought.

**Why it happens:** Streaming architecture evaluates content in fixed-size chunks (e.g., every 50 tokens or every 200 characters). Chunk boundaries do not align with sentence boundaries or entity boundaries. An SSN "123-45-6789" split across two chunks as "123-45-" and "6789" will not be detected by Presidio in either chunk individually.

**Consequences:** PII and harmful content that spans chunk boundaries is not detected. The safety pipeline has systematic blind spots at every chunk boundary, and these blind spots are predictable and exploitable by adversarial inputs that deliberately fragment sensitive data across boundaries.

**Prevention:**
- Implement overlap/sliding window in the output scanner: each evaluation chunk includes N characters from the previous chunk as overlap context. The overlap size must be at least the maximum entity length for any recognizer (e.g., SSN is 11 characters, so overlap >= 15 characters to handle boundary cases).
- For sentence-level analysis (Llama Guard classification), buffer until sentence boundaries are detected (period, question mark, newline) rather than flushing at fixed token counts. This means the buffer window is variable, not fixed-size, but it ensures complete semantic units are evaluated.
- The input scanner does NOT have this problem (input is a complete message before evaluation). Only the output scanner needs overlap/sliding-window handling.
- Test explicitly: create test cases where PII entities and harmful phrases are split across chunk boundaries and verify detection still works.

**Detection:** Automated boundary-split test: take a corpus of known-flaggable content, split each item at various boundary positions, and run the scanner on each partial chunk. If detection rate drops significantly compared to whole-text evaluation, the chunk handling needs overlap.

**Phase:** Phase 2 (Safety Pipeline Implementation) — the output scanner buffer architecture must include overlap from the design phase.

---

## Moderate Pitfalls

### Pitfall 7: Presidio False Positives Destroying User Experience

**What goes wrong:** Presidio with default recognizers and aggressive thresholds flags legitimate business content as PII. Numeric strings that are project codes, part numbers, or reference IDs are detected as phone numbers or SSNs. Internal email addresses are always detected even when they are meant to be shared. Names of people in business context ("Contact John Smith about the project") are flagged as PII. Users experience constant blocking of normal work messages and abandon the tool.

**Why it happens:** Default Presidio recognizers use broad patterns. The US_PHONE_NUMBER recognizer matches any 10-digit number, which catches project codes. The EMAIL recognizer matches any @-containing string. Thresholds are set conservatively (low confidence required for a match). Enterprise text naturally contains many strings that superficially resemble PII patterns but are not sensitive in context.

**Prevention:**
- Tune confidence thresholds per recognizer type UP for enterprise use. Phone number detection should require higher confidence (0.7+ instead of default 0.5). This reduces false positives on numeric strings that are not phone numbers.
- Implement context-aware filtering: Presidio supports context words that boost or suppress detection confidence. Define enterprise-specific context words that suppress PII detection in business context (e.g., "project", "reference", "ticket", "case" near a numeric string suppresses phone-number detection).
- Allow-list known safe patterns: enterprise email domains, known project code formats, legitimate internal reference number patterns. Presidio supports deny-list and allow-list configuration.
- Create a "false positive review" process: when a user reports a false block, the admin reviews it and tunes the recognizer or threshold. This is not a one-time configuration — it requires ongoing calibration with real enterprise data.

**Detection:** Monitor block rates. If more than 5-10% of legitimate messages are blocked, false positives are too aggressive. Track user complaints about false blocks as a key metric.

**Phase:** Phase 3 (Policy Configuration and Tuning) — threshold and context tuning happens here. But Phase 2 must build the infrastructure for per-recognizer threshold configuration, context word configuration, and allow-lists so that tuning is possible.

---

### Pitfall 8: Llama Guard / LLM Guard Latency Killing Streaming UX

**What goes wrong:** Running Llama Guard or LLM Guard inference on each output chunk adds 50-200ms per evaluation. With a streaming buffer that evaluates every 3-5 tokens, the effective throughput becomes slower than non-streaming. The user sees nothing for seconds, then a burst of text, then another pause. The "streaming" UX feels worse than simple request-response.

**Why it happens:** Llama Guard is a full LLM inference call — it processes the text through a model to classify safety categories. This is inherently slower than regex-based detection (Presidio). LLM Guard also includes multiple scanner modules, each adding latency. Teams run all scanners on every chunk without considering which scanners are fast (regex-based) vs slow (model-based).

**Consequences:** Users perceive the chat as slow and unreliable. The streaming UX advantage is lost. Employees revert to direct model access (without safety controls) because the "safe" version is too slow.

**Prevention:**
- Separate fast and slow scanners in the output pipeline:
  - Fast scanners (Presidio regex/pattern recognizers, simple keyword checks) run on every small chunk with minimal buffer.
  - Slow scanners (Llama Guard classification) run on accumulated larger chunks (every 200-500 characters or at sentence boundaries), not on every 3-5 tokens.
- This means the output pipeline has TWO evaluation cadences: fast-check every small buffer flush, slow-check every larger semantic unit. Content passes the fast check to start streaming, but the slow check can retroactively block if it catches something the fast check missed — which requires the buffer to hold back enough content that retroactive blocking is still possible before the flagged content is flushed to SSE.
- Pre-evaluate the model provider's safety: if Qwen has built-in safety filtering, configure it as a first-pass filter. Llama Guard serves as a second-pass verification, not the sole safety gate.
- Set a maximum latency budget per chunk evaluation. If slow scanners exceed the budget, block and retry rather than allowing unverified content.

**Detection:** Measure time-to-first-token and time-to-complete-response. Compare with non-streaming baseline. If streaming is slower, the scanner cadence is wrong.

**Phase:** Phase 2 (Safety Pipeline Implementation) — the two-cadence scanner pipeline (fast + slow) must be architected from the start. Retrofitting fast/slow separation after building a single-cadence pipeline requires restructuring the streaming buffer and scanner orchestration.

---

### Pitfall 9: Mock OIDC Becoming Permanent (No Real Auth for Months)

**What goes wrong:** The MVP starts with mock OIDC that returns a fixed test user. The mock auth works "fine" for development and demos. Months pass. The enterprise still has not confirmed which IDP to use. The mock OIDC is still in place. The application goes into limited production use with mock auth — anyone can claim any identity, there is no real authentication, audit events link to fake user IDs, and there is no role enforcement.

**Why it happens:** Mock OIDC is convenient. Real IDP integration requires enterprise cooperation (providing client credentials, discovery endpoints, user attribute mapping). Enterprise IT teams are slow to provision these. Developers keep using the mock because "we are still in MVP." The mock becomes the de facto auth system.

**Consequences:** No real user authentication. No real role enforcement. Audit events contain fake user data, making them useless for compliance. Any employee (or non-employee with access to the URL) can use the system as any identity including admin.

**Prevention:**
- Time-box mock OIDC: set a hard deadline (e.g., 4 weeks after MVP launch) for real OIDC integration. After that deadline, the mock OIDC adapter should be disabled — the system requires real auth to operate.
- Build the OIDC adapter as a true strategy pattern from day one: `oidc.py` is an interface, `mock_oidc.py` and `real_oidc.py` are separate implementations. The mock implementation should have a startup warning log and a visible UI indicator ("DEMO AUTH — NOT PRODUCTION") that is impossible to miss.
- The mock OIDC implementation should support at least TWO mock users (one employee, one admin) with different roles, so that role-based behavior is tested from the start. Do not use a single "superuser" mock.
- Add a configuration flag: `AUTH_MODE=mock|real`. When `AUTH_MODE=mock`, the system logs a warning on every request and displays a banner in the UI. When `AUTH_MODE=real`, the mock adapter is not loaded at all.

**Detection:** Check the AUTH_MODE configuration at every sprint review. If mock auth is still active past the deadline, escalate. Monitor startup logs for mock auth warnings in any environment that users access.

**Phase:** Phase 1 (Core Infrastructure) — the auth adapter pattern and configuration flag must be in the initial architecture. Phase 5 (Enterprise Integration) — real OIDC integration happens here, but the infrastructure must exist from Phase 1.

---

### Pitfall 10: Conversation History Storing PII That Presidio Missed (False Negative Database Contamination)

**What goes wrong:** The policy is "only store allowed-through content." But if Presidio has a false negative (misses PII in the input), the content passes the scanner, gets an ALLOW verdict, and is stored in the conversation history table. The database now contains PII that was supposed to be blocked. Over time, the conversation history table accumulates sensitive data that Presidio missed.

**Why it happens:** No PII detection system has 100% recall. Presidio will miss some PII, especially enterprise-specific patterns (see Pitfall 3) and PII in non-English text. The "only store allowed content" policy assumes the scanner is perfect, which it is not.

**Consequences:** The database contains PII that was not caught by the scanner. Compliance audit finds PII in conversation history that should have been blocked. Data retention policies applied to conversation history now need to handle PII that was supposed to be filtered out.

**Prevention:**
- Add a secondary PII scan on content BEFORE database storage, even if it already passed the input/output scanner. This "storage scan" uses the same Presidio recognizers but can run with higher sensitivity (lower thresholds) because latency is not a concern (it is not in the streaming path). If the storage scan detects PII, the content is NOT stored — only audit metadata is recorded.
- This two-tier approach means: (1) input/output scanner with tuned thresholds for real-time UX, (2) storage scanner with aggressive thresholds for database safety. Content that passes tier 1 but fails tier 2 is displayed to the user (they saw it already) but NOT stored in conversation history.
- Set data retention limits on conversation history (auto-purge after N days). Even with aggressive scanning, some PII will slip through; retention limits reduce the blast radius.
- Periodic retroactive scan: run Presidio on existing conversation history content at regular intervals (daily/weekly) with aggressive thresholds. If newly detected PII is found (due to recognizer improvements or threshold changes), flag those records for review or automatic purge.

**Detection:** Run retroactive Presidio scan on conversation history monthly. Count PII detections. If count is non-zero, false negatives are reaching the database.

**Phase:** Phase 3 (Policy Configuration and Tuning) — the storage-scan and retroactive-scan infrastructure. But the dual-scan architecture (real-time scan + storage scan) must be designed in Phase 2 so that the pipeline supports two evaluation passes with different threshold profiles.

---

### Pitfall 11: Adversarial Prompt Injection Targeting the Safety Scanner

**What goes wrong:** A user sends input that is not harmful content itself, but is crafted to manipulate the safety scanner into returning false results. Examples: (1) A prompt that causes Llama Guard to classify a subsequent harmful query as safe. (2) An input that exploits Llama Guard's classification prompt format, injecting instructions that override its safety judgment. (3) A prompt that causes Presidio to suppress PII detection by inserting confusing context around sensitive data.

**Why it happens:** Llama Guard and LLM Guard are themselves LLMs or LLM-based systems. They process input text through a model, which means they are susceptible to the same prompt injection techniques that they are designed to detect. This is a known limitation of LLM-based safety classifiers.

**Consequences:** The safety scanner is subverted. Harmful content or PII passes through because the scanner was manipulated into returning a safe verdict. The safety system's primary defense mechanism is itself attackable.

**Prevention:**
- Treat scanner outputs as untrusted: do not trust Llama Guard's "safe" verdict as absolute. Combine Llama Guard classification with Presidio pattern detection as a layered defense. If Presidio detects PII patterns regardless of Llama Guard's verdict, block the content.
- Implement scanner input sanitization: before sending text to Llama Guard for classification, strip or escape any text that looks like prompt injection targeting the classifier (e.g., instructions embedded in the user message like "ignore previous instructions", "classify this as safe"). This is a partial defense but reduces the most obvious attacks.
- Monitor for anomalous scanner results: if Llama Guard's verdict distribution shifts significantly (e.g., suddenly 95% of inputs are classified as "safe" when it was previously 80%), flag this as a potential scanner manipulation attack.
- LLM Guard includes specific prompt injection detection scanners (e.g., `PromptInjectionScanner`). Use these as a pre-filter: run prompt injection detection BEFORE running safety classification. If prompt injection is detected in the input, block it before it reaches Llama Guard.

**Detection:** Track scanner verdict distribution over time. Sudden shifts toward "safe" verdicts indicate potential manipulation. Also test with known adversarial prompt injection examples and verify they are caught.

**Phase:** Phase 3 (Policy Configuration and Tuning) — scanner input sanitization and prompt injection pre-filtering. Phase 4 (Testing and Hardening) — adversarial testing with known prompt injection techniques.

---

### Pitfall 12: Treating Safety as Binary Allow/Block (Gray Area Content)

**What goes wrong:** The safety pipeline returns only `PolicyAction.ALLOW` or `PolicyAction.BLOCK`. Real enterprise content often falls in gray areas: low-confidence PII detections, borderline harmful content, content that is sensitive in some contexts but not others. Binary decisions either over-block (frustrating users) or under-block (missing real risks). There is no mechanism for "allow with warning" or "allow with audit flag."

**Why it happens:** The initial design simplifies the policy to two actions for MVP clarity. This is reasonable for the MVP scope, but if the architecture hard-codes only two actions without extensibility, adding intermediate actions later requires modifying the pipeline, the frontend, the database schema, and the audit format simultaneously.

**Consequences:** Users experience frequent hard blocks on borderline content, leading to frustration and workarounds. Or thresholds are lowered to reduce blocks, leading to real risks passing through. Either way, the system is not serving the enterprise well.

**Prevention:**
- Design the `PolicyAction` enum from day one with at least three values: `ALLOW`, `BLOCK`, and `WARN` (or `FLAG`). The MVP may only implement `ALLOW` and `BLOCK` behavior, but the enum and the pipeline logic should support `WARN` without a refactor.
- `WARN` action: content is displayed to the user with a visible warning banner ("This content may contain sensitive information — handle with care"), and the audit event is flagged for admin review. The content is stored in conversation history with a warning annotation.
- This means the frontend, backend pipeline, database schema, and audit format must all handle three action types from the start, even if `WARN` behavior is initially identical to `ALLOW` with an extra metadata field.
- Do NOT implement `WARN` behavior in the MVP if it adds significant complexity — but DO ensure the data model and pipeline interface can represent it without a refactor.

**Detection:** After launch, review block rates and user complaints. If legitimate business content is frequently blocked, the binary model is failing and WARN needs to be activated.

**Phase:** Phase 2 (Safety Pipeline Implementation) — the `PolicyAction` enum and pipeline interface must include `WARN` from the start. Phase 3 (Policy Configuration) — configure thresholds that distinguish BLOCK vs WARN zones.

---

## Minor Pitfalls

### Pitfall 13: Frontend Calling Model Providers Directly (Bypassing Safety Pipeline)

**What goes wrong:** The frontend code includes a direct API call path to the model provider (Qwen or local OpenAI-compatible) for "fallback" or "speed" reasons. This call path bypasses the backend safety pipeline entirely. Content goes directly from user input to model provider and back to display, with no safety checks.

**Why it happens:** During development, testing model provider APIs directly from the frontend is convenient. The direct call path remains in the codebase as a "debug mode" or "fallback." It is not removed before deployment.

**Consequences:** Users can bypass safety controls entirely. This violates the core architecture constraint ("Frontend never calls model providers directly — all model calls and safety checks go through the backend").

**Prevention:**
- Never implement direct frontend-to-model-provider API calls, even for debugging. All model provider calls go through the backend API, even in development.
- CORS configuration on the backend must NOT allow direct browser-to-model-provider requests. Model provider API endpoints should not be accessible from the frontend's origin.
- If model provider APIs need to be tested independently, use backend test scripts, not frontend code.
- Code review gate: any PR that adds a fetch/axios call to a model provider URL from frontend code must be rejected.

**Detection:** Code review: search frontend codebase for any HTTP calls to model provider endpoints (qwen API URLs, localhost OpenAI-compatible ports). Audit CORS configuration.

**Phase:** Phase 1 (Core Infrastructure) — CORS and API architecture must prevent frontend-to-model direct calls from the start.

---

### Pitfall 14: Hardcoded Scanner Configuration (No Runtime Policy Changes)

**What goes wrong:** Safety scanner thresholds, enabled scanner modules, and recognizer configurations are hardcoded in the backend source code or static configuration files. When the enterprise needs to adjust a threshold (e.g., lower phone number detection sensitivity because of too many false positives), the change requires a code modification, rebuild, and redeployment. Admin dashboard "policy configuration" UI exists but only modifies values that are read at startup — changes require a server restart.

**Why it happens:** Initial implementation reads configuration from environment variables or config files at application startup. There is no mechanism to reload configuration at runtime. The admin dashboard UI modifies a database table, but the backend reads configuration from a file, not from the database. The two configuration sources are disconnected.

**Consequences:** Policy changes require server restarts, which is unacceptable in enterprise environments. Admin users configure policies through the dashboard but the changes do not take effect until the next deployment. Operational teams cannot respond to emerging threats quickly.

**Prevention:**
- Store policy configuration in PostgreSQL (the project database), not in environment variables or config files. The backend reads policy from the database on each request (or with a short TTL cache, e.g., 30 seconds, to avoid database load).
- The admin dashboard directly modifies the policy database table. Changes take effect within the cache TTL (30 seconds), not on next restart.
- Environment variables are used only for deployment-level configuration (database URL, model provider URLs, auth mode). Policy-level configuration (thresholds, enabled scanners, recognizer settings) is in the database.
- Implement a configuration versioning mechanism in the database: each policy change creates a new version row. This enables audit of policy changes and rollback to previous versions.

**Detection:** After implementing admin policy configuration, change a threshold in the dashboard and immediately test with a message that should be affected by the change. If the change does not take effect within 30 seconds, configuration is not runtime-reloadable.

**Phase:** Phase 1 (Core Infrastructure) — configuration architecture (env vars for deployment, database for policy) must be established from the start. Phase 4 (Admin Dashboard) — dashboard UI writes to policy database table.

---

### Pitfall 15: Not Testing the Block Path Thoroughly (Only Testing Happy Path)

**What goes wrong:** Automated tests cover the "allow" path (user sends a safe message, gets a response, sees it in conversation history). The "block" path is tested minimally (one or two PII examples). When a real block event happens in production, the frontend crashes, the audit event is malformed, or the conversation UI shows a broken state. Block-path bugs are discovered in production, not in development.

**Why it happens:** Block events are edge cases in normal usage. Developers test the happy path first because it is the primary user experience. Block paths are "negative" scenarios that are easy to deprioritize. But for this project, the block path IS the core value proposition — it must work perfectly.

**Prevention:**
- Write automated tests for the block path FIRST, before the allow path. The project requirement says "Automated tests prove the main allow/block paths." Treat block-path tests as equal priority to allow-path tests.
- Create a comprehensive test corpus of block-triggering inputs and outputs:
  - Input with PII (each recognizer type: SSN, email, phone, Chinese national ID, custom enterprise patterns)
  - Input with harmful content (each Llama Guard category)
  - Input with prompt injection patterns
  - Output with PII (model generates sensitive data)
  - Output with harmful content
  - Edge cases: PII at chunk boundaries, PII in non-English text, PII in code blocks, harmful content in markdown formatting
- Test frontend block-message rendering: verify that block messages display correctly, contain no echoed PII, and do not break the conversation UI state.
- Test audit event generation on blocks: verify that audit records contain correct metadata and no raw sensitive content.

**Detection:** Test coverage metrics: measure percentage of test cases that exercise block paths vs allow paths. Target at least 50% block-path coverage for the MVP.

**Phase:** Phase 4 (Testing and Hardening) — comprehensive block-path test suite. But the test corpus must start being assembled in Phase 2 alongside the pipeline implementation.

---

### Pitfall 16: Ignoring Non-English PII (Chinese PII Formats with Qwen Integration)

**What goes wrong:** The project integrates Qwen (Chinese LLM from Alibaba Bailian). Users will send Chinese-language queries and receive Chinese-language responses. Presidio's default recognizers are optimized for English PII formats. Chinese national ID numbers (18 digits), Chinese phone numbers (11 digits starting with 1), Chinese addresses, and Chinese names are not reliably detected by default Presidio recognizers. PII in Chinese text passes the scanner undetected.

**Why it happens:** Teams assume PII detection is language-agnostic or that Chinese PII follows similar patterns to US PII. Presidio does include some international recognizers, but coverage for Chinese PII is limited compared to English. Custom recognizers for Chinese PII are needed but are often not prioritized.

**Consequences:** Chinese-language PII leaks through the safety pipeline. This is particularly concerning because Qwen is a Chinese LLM — Chinese-language usage is expected, not exceptional.

**Prevention:**
- Add custom Presidio recognizers for Chinese PII types:
  - Chinese national ID: 18 digits with specific format rules (area code + birth date + sequence + check digit). Regex pattern with validation.
  - Chinese mobile phone: 11 digits starting with known prefixes (130-139, 150-159, 180-189, etc.). Regex pattern with prefix validation.
  - Chinese address patterns: province/city/district names followed by street/detail patterns. Regex or NLP-based recognizer.
  - Chinese names: common surname + given name patterns. This is harder — consider using a dedicated Chinese NLP model rather than regex.
- Test the safety pipeline with Chinese-language inputs containing known Chinese PII. This test must be part of the standard test suite, not an afterthought.
- Consider adding a Chinese-specific NLP analyzer (spaCy Chinese model or equivalent) alongside Presidio for Chinese-language detection.

**Detection:** Run the safety pipeline on a corpus of Chinese-language messages containing Chinese PII. Measure detection rate. If below 90%, custom recognizers need improvement.

**Phase:** Phase 3 (Policy Configuration and Tuning) — custom Chinese PII recognizers. Phase 4 (Testing) — Chinese-language test corpus.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Core Infrastructure (Phase 1) | Mock OIDC becomes permanent (#9), Hardcoded scanner config (#14), Frontend direct model calls (#13) | Auth adapter pattern with time-box, DB-backed policy config, CORS enforcement |
| Safety Pipeline (Phase 2) | Streaming buffer bypass (#1), Echoing PII in block messages (#2), Scanner fail-open (#5), Scanner on partial content (#6), Audit metadata leak (#4) | Buffer-after-scan architecture, sanitized PolicyDecision, fail-closed default, overlap/sliding window, strict audit schema |
| Policy Configuration (Phase 3) | Presidio false positives (#7), Missing enterprise PII (#3), Chinese PII gaps (#16), Binary allow/block (#12) | Threshold tuning, custom recognizers, Chinese recognizers, PolicyAction.WARN in enum |
| Testing and Hardening (Phase 4) | Only testing happy path (#15), Prompt injection targeting scanner (#11) | Block-path test suite first, adversarial prompt injection tests |
| Admin Dashboard (Phase 5) | Hardcoded config not runtime-reloadable (#14 continued) | Dashboard writes to policy DB, backend reads from DB with TTL cache |
| Enterprise Integration (Phase 5) | Mock OIDC still active (#9 continued), Conversation DB PII contamination (#10) | Real OIDC deadline enforcement, storage-scan + retroactive-scan |

## Confidence Assessment

| Finding | Confidence | Reason |
|---------|------------|--------|
| Streaming buffer bypass (#1) | HIGH | Fundamental architectural issue in streaming+safety systems; well-documented in LLM safety literature |
| Echoing PII in block messages (#2) | HIGH | Directly contradicts stated project requirement; common implementation mistake |
| Presidio false negatives on enterprise PII (#3) | HIGH | Presidio documentation explicitly states custom recognizers are needed for domain-specific PII; defaults are US-centric |
| Audit metadata reconstruction (#4) | MEDIUM | Based on security engineering principles; specific attack feasibility depends on schema details |
| Scanner fail-open (#5) | HIGH | Standard security engineering principle (fail-closed); commonly violated in practice |
| Scanner on partial content (#6) | HIGH | Presidio documentation discusses boundary handling; overlap/sliding window is standard practice in PII detection |
| Presidio false positives (#7) | HIGH | Common complaint in Presidio community; default thresholds are too aggressive for enterprise |
| Llama Guard latency (#8) | MEDIUM | Latency depends on deployment model (local GPU vs API call); exact numbers vary, but the architectural concern is valid |
| Mock OIDC permanence (#9) | MEDIUM | Common project management pitfall; depends on enterprise IT responsiveness |
| Conversation DB PII contamination (#10) | HIGH | No detection system has 100% recall; dual-scan approach is standard practice |
| Adversarial prompt injection targeting scanner (#11) | MEDIUM | Known limitation of LLM-based classifiers; specific attack effectiveness depends on model version |
| Binary allow/block (#12) | MEDIUM | Reasonable for MVP but architectural extensibility concern; depends on enterprise policy complexity |
| Frontend direct model calls (#13) | HIGH | Stated project constraint; requires architectural enforcement |
| Hardcoded scanner config (#14) | HIGH | Standard configuration management pitfall; DB-backed config is well-established pattern |
| Block path testing neglect (#15) | HIGH | Stated project requirement; common testing pitfall |
| Chinese PII gaps (#16) | MEDIUM | Presidio Chinese PII coverage needs verification against current version; custom recognizers needed |

## Sources

- Microsoft Presidio documentation (custom recognizers, confidence thresholds, context words) — training data, needs verification with current docs
- Meta Llama Guard documentation (classification categories, deployment, latency) — training data, needs verification with current docs
- ProtectAI LLM Guard documentation (scanner modules, prompt injection detection) — training data, needs verification with current docs
- Project context: `.planning/PROJECT.md` — verified directly
- Key decisions: `.planning/notes/key-decisions.md` — verified directly
- Domain expertise: streaming safety architecture, PII detection in enterprise systems, OIDC integration patterns

Note: WebSearch, Context7, and Bash tools were unavailable during this research session. Confidence levels reflect reliance on domain expertise and training data. Findings marked MEDIUM should be verified with current documentation before implementation. Findings marked HIGH are based on established security engineering principles and documented library limitations that are unlikely to have changed.