# Requirements: Enterprise AI Chat MVP

**Defined:** 2026-05-21
**Core Value:** Prove that employees can use AI chat safely in a controlled enterprise environment — the safety pipeline must work reliably and block sensitive or non-compliant content without echoing it.

## v1 Requirements

### Authentication

- [ ] **AUTH-01**: Employee can sign in through OIDC authentication (mock OIDC for MVP with fixed test user)
- [ ] **AUTH-02**: Backend routes have access to authenticated user identity (user ID, role)
- [ ] **AUTH-03**: Role distinction between employee (chat access) and admin (config + audit access)

### Chat

- [ ] **CHAT-01**: Employee can select an allowed model provider (Qwen or local OpenAI-compatible)
- [ ] **CHAT-02**: Employee can send a chat message and receive a response through the backend
- [ ] **CHAT-03**: Chat responses stream to the frontend with a safety buffer that prevents unsafe tokens from being displayed before safety checks complete

### Safety Pipeline

- [ ] **SAFE-01**: Input safety filtering runs before every model call, checking PII, sensitive data, prompt injection, jailbreak attempts, and harmful content
- [ ] **SAFE-02**: Output safety filtering runs before every response display, checking model responses for the same risk categories
- [ ] **SAFE-03**: Policy violations block the full input or output — no partial redaction or display
- [ ] **SAFE-04**: Block messages explain the risk category and action taken without echoing the detected sensitive content
- [ ] **SAFE-05**: Audit event metadata is recorded for every allow and block decision
- [ ] **SAFE-06**: Audit events contain metadata only (event ID, timestamp, user ID, model, risk categories, policy action) — never raw prompts, raw model outputs, or full PII values
- [ ] **SAFE-07**: Scanner failures (crash, timeout, error) default to BLOCK (fail-closed semantics) — content never passes unfiltered
- [ ] **SAFE-08**: Custom Presidio recognizers cover enterprise-specific PII types (employee IDs, project codes, Chinese national IDs)

### Conversation History

- [ ] **HIST-01**: Employee can browse a list of past conversations
- [ ] **HIST-02**: Employee can resume a past conversation and continue chatting
- [ ] **HIST-03**: Database stores only allowed-through message content — blocked content is never stored in conversation records
- [ ] **HIST-04**: Blocked conversations generate audit event entries but no Message rows in the database

### Admin Dashboard

- [ ] **ADMN-01**: Admin can view audit event metadata through a dashboard UI (risk categories, policy actions, timestamps, user and model info)
- [ ] **ADMN-02**: Admin can configure model providers and credentials through a dashboard UI
- [ ] **ADMN-03**: Admin can configure policy thresholds and enabled scanner modules through a dashboard UI

### Testing

- [ ] **TEST-01**: Automated tests prove the main allow path (safe input → model call → safe output → display)
- [ ] **TEST-02**: Automated tests prove the input block path (unsafe input → no model call → block message → audit event)
- [ ] **TEST-03**: Automated tests prove the output block path (unsafe output → no display → block message → audit event)
- [ ] **TEST-04**: Automated tests prove fail-closed behavior (scanner crash/error → content blocked → audit event)
- [ ] **TEST-05**: Security test fixtures include PII, sensitive business data, prompt injection attempts, jailbreak requests, harmful content, and unsafe model output

## v2 Requirements

### Real OIDC Integration

- **AUTH-04**: Real enterprise OIDC provider integration (Okta, Azure AD, Keycloak, or LDAP) when IDP is confirmed
- **AUTH-05**: User department or group information available from real IDP

### Advanced Safety

- **SAFE-09**: Llama Guard 3 model-based guardrails as separate inference server (higher accuracy, heavier infrastructure)
- **SAFE-10**: Data classification-aware filtering with enterprise taxonomy labels (Confidential, Internal, Restricted, Public)
- **SAFE-11**: Content hashing in audit logs for correlation (only if explicitly approved by enterprise policy)

### Streaming Enhancements

- **CHAT-04**: Non-streaming fallback mode when safety buffer is unavailable or model provider doesn't support streaming
- **CHAT-05**: Streaming buffer threshold tuning based on empirical latency vs safety trade-offs

### Admin Enhancements

- **ADMN-04**: Admin can manage multiple organization contexts (multi-tenant)
- **ADMN-05**: Advanced analytics dashboard beyond audit viewer

## Out of Scope

| Feature | Reason |
|---------|--------|
| Anonymous chat access | Enterprise requirement — all users must be authenticated |
| Frontend model provider calls | Safety enforcement must happen on backend only |
| Redaction with partial display | MVP blocks full content; partial display increases compliance risk |
| Model provider marketplace | Complex, not core to proving safety pipeline |
| Multi-provider routing (cost/latency) | Single model selection sufficient for demo |
| Automatic provider fallback | Adds complexity without proving safety value |
| Custom filtering model training | Use existing open-source libraries |
| Commercial DLP integration | Beyond MVP scope |
| Multi-tenant org management | Single enterprise context for MVP |
| Raw prompt/output storage | Database and logs must never contain sensitive content |
| Fine-grained RBAC | Two roles (employee/admin) sufficient for MVP |
| User-supplied provider credentials | Admin-only configuration |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| CHAT-01 | Phase 2 | Pending |
| CHAT-02 | Phase 2 | Pending |
| CHAT-03 | Phase 4 | Pending |
| SAFE-01 | Phase 2 | Pending |
| SAFE-02 | Phase 2 | Pending |
| SAFE-03 | Phase 2 | Pending |
| SAFE-04 | Phase 2 | Pending |
| SAFE-05 | Phase 2 | Pending |
| SAFE-06 | Phase 2 | Pending |
| SAFE-07 | Phase 2 | Pending |
| SAFE-08 | Phase 2 | Pending |
| HIST-01 | Phase 3 | Pending |
| HIST-02 | Phase 3 | Pending |
| HIST-03 | Phase 3 | Pending |
| HIST-04 | Phase 3 | Pending |
| ADMN-01 | Phase 4 | Pending |
| ADMN-02 | Phase 4 | Pending |
| ADMN-03 | Phase 4 | Pending |
| TEST-01 | Phase 2 | Pending |
| TEST-02 | Phase 2 | Pending |
| TEST-03 | Phase 2 | Pending |
| TEST-04 | Phase 2 | Pending |
| TEST-05 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-21*
*Last updated: 2026-05-21 after initial definition*