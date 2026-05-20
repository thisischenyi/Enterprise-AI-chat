# Feature Landscape

**Domain:** Enterprise AI chat with safety filtering
**Researched:** 2026-05-21
**Confidence caveat:** WebSearch and Bash tools were denied during this research session. Findings are based on training knowledge of enterprise AI chat products (Microsoft Copilot, ChatGPT Enterprise, Google Gemini for Business, Amazon Q, etc.) and the project's own SPEC.md and PROJECT.md. Confidence levels are accordingly MEDIUM for table stakes (well-established patterns) and LOW for differentiators (harder to verify without live research). All claims should be validated against current market offerings during phase-specific research.

## Table Stakes

Features users expect. Missing = product feels incomplete or unsafe for enterprise deployment.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Authentication (OIDC/SSO) | Enterprise mandates authenticated access; anonymous chat is a security violation. Every enterprise AI product (Copilot, ChatGPT Enterprise, Gemini for Business) requires login. | Med | MVP uses mock OIDC; real provider adapter is a follow-up. Two roles (employee/admin) sufficient for MVP. |
| Chat interface with model selection | Core interaction. Users need to pick a model and send messages. This is the defining feature of any AI chat product. | Low | Standard React chat UI. Model selector dropdown. Message input + response display. |
| Input content filtering | Enterprise compliance requires detecting PII, sensitive data, prompt injection, and harmful content before it reaches the model. Azure OpenAI, ChatGPT Enterprise all do this. | High | Presidio for PII/data classification + LLM Guard for jailbreak/harmful content. Multiple scanners coordinated in a pipeline. |
| Output content filtering | Model responses can contain sensitive data, harmful content, or policy violations. Enterprises require output filtering just as strictly as input filtering. Azure OpenAI does this by default. | High | Same scanner infrastructure as input, applied to model output. Must not echo blocked content in the replacement message. |
| Block/allow with safe replacement messages | When content is blocked, the user must see a clear explanation (risk category, action taken) without the sensitive text being echoed back. This is a compliance requirement, not a UX nicety. | Med | PolicyAction enum (ALLOW/BLOCK). Blocked messages explain category but never reproduce the flagged content. |
| Audit logging (metadata only) | Enterprises need traceability for compliance, incident response, and policy effectiveness measurement. Audit logs are mandatory in every enterprise AI deployment. | Med | Event metadata (user, session, model, direction, risk categories, action) but no raw prompts, outputs, or PII values. |
| Conversation history persistence | Users expect to resume past conversations. Without it, the product feels disposable and not enterprise-grade. | Med | Only store content that passed safety checks. Blocked messages get audit entries, not conversation rows. |
| Streaming responses | Non-streaming chat feels sluggish. Every modern AI chat product streams responses. Enterprise users will notice latency immediately. | Med | Streaming with safety buffer: output streams to user but safety checks run with a buffer to intercept unsafe content before display. This is the hardest UX problem. |
| Admin model configuration | Admins must control which models are available and how they are connected. Without this, the system is unmanageable in an enterprise context. | Low | Admin UI for provider IDs, credentials, and endpoints. Backend-only credential storage. |
| Admin policy configuration | Policy thresholds, enabled scanner modules, and data classification categories must be adjustable. Static hardcoded policies are not enterprise-ready. | Low | Admin UI toggles for scanner modules, threshold sliders, classification category selection. |

## Differentiators

Features that set this product apart from generic AI chat. Not universally expected, but valued in an enterprise safety context.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Streaming with safety buffer | Most enterprise AI products either stream unsafely or buffer the entire response (slow). A streaming + buffered safety check gives responsive UX while maintaining safety. This is genuinely difficult and few products do it well. | High | Requires a chunk-by-chunk safety evaluation with a lookahead buffer. If a chunk is flagged, intercept it before the browser receives it. WebSocket or SSE with backend-side buffering logic. |
| Non-echoing block messages | Many products reveal what was detected (e.g., "your message contained a Social Security Number: 123-45-6789"). This product explicitly avoids echoing sensitive content, showing only the risk category and action. This is a genuine compliance differentiator. | Low | Simple to implement but philosophically important. The SPEC mandates it and the project boundaries enforce it. |
| Data classification-aware filtering | Most PII tools detect individual PII types. This product also applies enterprise data classification labels (Confidential, Internal, Restricted, Public) to content, enabling organization-specific policy enforcement. | Med | Presidio custom recognizers can detect classification-indicating patterns. Policy thresholds vary by classification level. Requires enterprise to define its classification taxonomy first. |
| Multi-provider support (cloud + self-hosted) | Supporting both a cloud LLM (Qwen via Bailian) and self-hosted local models (OpenAI-compatible API) in the same product gives enterprises flexibility that single-provider products lack. | Low | Provider adapter pattern. QwenProvider and OpenAICompatibleProvider behind a common interface. Selection is per-conversation, not global routing. |
| Safe conversation storage model | Storing only allowed-through content (blocked content exists only as audit metadata) is unusual. Most products store everything including flagged content. This product's database never contains non-compliant data. | Med | Requires safety pipeline to gate database writes. Message rows only created after PolicyAction.ALLOW. Blocked messages recorded as audit events only. |
| Scanner interface abstraction | DataProtectionScanner and LLMGuardrailScanner as interfaces, not concrete implementations. This lets the enterprise swap filtering libraries without touching the pipeline logic. | Low | Strategy/adapter pattern. Valuable for long-term maintainability and for responding to library deprecation or license changes. |
| Policy configuration UI | Not just hardcoded thresholds -- an admin UI where scanner modules can be toggled on/off, thresholds adjusted, and classification categories configured. Most enterprise AI tools expose this only through API or config files. | Med | Admin dashboard with forms for each scanner module. Changes persisted to database, applied at runtime. |
| Audit dashboard for metadata | A UI where admins can browse audit events (who, when, which model, which direction, risk categories, action taken) without seeing raw content. Most products either expose raw content or have no UI at all. | Med | Admin-facing audit viewer with filtering and pagination. No raw content display, ever. |

## Anti-Features

Features to explicitly NOT build. These are documented in PROJECT.md Out of Scope and SPEC.md boundaries.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Anonymous/guest access | Enterprise requires authentication for compliance and audit traceability. Anonymous access is a security violation. | Require OIDC login for all routes. No public-facing chat. |
| Direct model API access from frontend | Frontend calling model providers directly bypasses all safety controls. This defeats the entire purpose of the product. | All model calls go through backend. Frontend only receives filtered responses. |
| Redaction with partial display | Showing partial content (e.g., masking SSN but showing surrounding text) is complex, risky, and the project explicitly scopes it out. Blocked content is blocked fully. | Block entire input/output on any policy violation. Show safe replacement message. No partial content. |
| Multi-tenant organization management | This is a single-enterprise product. Multi-tenant adds complexity (org isolation, cross-org policy, billing) that doesn't prove the safety pipeline. | Single enterprise context. Two roles (employee/admin). No org switching. |
| Provider marketplace | A self-service marketplace where users add providers is complex (credential management, validation, sandboxing) and not core to proving safety. | Admin-only provider configuration. No user-facing marketplace. |
| Complex multi-provider routing | Routing by cost, latency, or policy across providers adds orchestration complexity that doesn't prove safety filtering works. | Simple per-conversation model selection. One model per chat session. |
| Automatic provider fallback | Fallback logic (try provider A, if error try provider B) adds error handling complexity without proving safety value. | Fail with error message if selected provider is unavailable. Admin can configure alternatives. |
| Custom model fine-tuning | Fine-tuning filtering models requires ML infrastructure, training data, and evaluation pipelines far beyond MVP scope. | Use existing open-source libraries (Presidio, Llama Guard) with default models and custom recognizers. |
| Commercial DLP integration | Integrating with enterprise DLP platforms (Symantec, Forcepoint) requires vendor-specific APIs, licensing, and deployment agreements. | Use open-source filtering wrapped behind internal interfaces. DLP adapters can be added later if needed. |
| Raw content in audit logs | Storing raw prompts, model outputs, or PII values in audit logs creates a compliance violation and a data breach risk in the audit system itself. | Log metadata only: risk categories, action, scanner names, counts. No raw content, ever. |
| Advanced analytics dashboards | Full analytics (trend charts, anomaly detection, policy effectiveness scoring) is valuable but not needed to prove the core safety pipeline works. | Simple audit event viewer with filtering. Analytics deferred. |
| Raw prompt storage for conversation memory | Storing raw prompts including sensitive content for long-term memory creates a data retention risk. | Store only allowed-through content. Blocked content lives only as audit metadata. |

## Feature Dependencies

```
Authentication (OIDC) --> Chat access (all chat features depend on auth)
Authentication --> Audit logging (audit events need user identity)
Chat interface --> Model selection --> Chat submission
Chat submission --> Input safety pipeline --> Model provider call (only if ALLOW)
Model provider call --> Output safety pipeline --> Response display (only if ALLOW)
Input safety pipeline --> Audit logging (both ALLOW and BLOCK events logged)
Output safety pipeline --> Audit logging (both ALLOW and BLOCK events logged)
Safety pipeline --> Conversation storage (only ALLOW results stored)
Safety pipeline --> Block message display (BLOCK results shown to user)
Admin configuration --> Model provider setup
Admin configuration --> Policy thresholds and scanner toggles
Streaming with safety buffer --> Output safety pipeline (buffering wraps output checks)
Data classification --> Policy configuration (categories defined in policy)
Conversation history --> Safety-gated storage (only allowed content persisted)
```

Critical dependency chain (the core flow):
```
Auth --> Chat UI --> Input Pipeline --> Model Call --> Output Pipeline --> Display
                     |                                    |
                     --> Audit (BLOCK)                     --> Audit (BLOCK or ALLOW)
                     --> Block message                     --> Block message OR stored message
```

## MVP Recommendation

Prioritize:
1. **Authentication (mock OIDC)** -- Gate for everything. Without auth, no enterprise context, no audit, no safety enforcement.
2. **Chat interface with model selection** -- The core user interaction. Must work before safety can be demonstrated on real traffic.
3. **Input/output safety pipeline** -- The product's defining value. Block/allow logic, safe replacement messages, and scanner coordination.
4. **Audit logging (metadata only)** -- Proves compliance. Without audit, blocked events are invisible and unverifiable.
5. **Admin model + policy configuration** -- Admins need to configure the system for it to be usable at all.
6. **Streaming with safety buffer** -- Key differentiator. Non-streaming MVP feels sluggish; streaming with safety is the UX challenge that proves the architecture.

Defer:
- **Conversation history persistence**: Medium complexity, not needed for first demo. Can build after core pipeline works.
- **Admin audit dashboard UI**: Admins can query audit events via API for MVP. UI can follow.
- **Data classification-aware filtering**: Requires enterprise taxonomy definition (open research question). Start with PII and harmful content detection; classification labels later.
- **Policy configuration UI**: Start with config-file-based thresholds. UI after core pipeline is stable.

## Phase-Specific Research Flags

- **Streaming with safety buffer**: This is the hardest feature. Need research on SSE/WebSocket patterns for buffered streaming, chunk-level safety evaluation timing, and how other products handle this. LOW confidence on implementation approach.
- **Data classification categories**: Which categories does the enterprise use? This is an open question in `.planning/research/questions.md`. Must be answered before classification-aware filtering can work.
- **Filter library selection**: Open todo in `.planning/todos/pending/filter-library-selection.md`. Exact libraries, versions, and deployment models need confirmation. This blocks the safety pipeline implementation.
- **Real OIDC provider**: Enterprise identity provider not yet determined. Mock OIDC works for MVP but real provider integration needs research when IDP is confirmed.

## Sources

- Project SPEC.md (internal): Detailed requirements, boundaries, and out-of-scope list
- Project PROJECT.md (internal): Core value proposition, constraints, and key decisions
- `.planning/notes/key-decisions.md` (internal): Four resolved decisions on auth, filtering, storage, deployment
- `.planning/todos/pending/filter-library-selection.md` (internal): Open research on exact filter libraries
- `.planning/research/questions.md` (internal): Open question on data classification categories
- Training knowledge of enterprise AI chat products (Microsoft Copilot, ChatGPT Enterprise, Google Gemini for Business, Amazon Q) -- MEDIUM confidence for table stakes, LOW confidence for differentiators
- No live web research was possible (WebSearch and Bash tools denied)

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Table stakes | MEDIUM | Well-established patterns across enterprise AI products, but cannot verify against current market |
| Differentiators | LOW | Streaming-with-safety-buffer and non-echoing block messages are claimed as differentiators based on training knowledge; need live verification |
| Anti-features | HIGH | Directly sourced from project SPEC.md and PROJECT.md Out of Scope lists -- no ambiguity |
| Dependencies | HIGH | Derived from project's documented core flow and architecture -- internally consistent |
| MVP prioritization | MEDIUM | Based on project priorities and common enterprise patterns; specific enterprise context may shift priorities |