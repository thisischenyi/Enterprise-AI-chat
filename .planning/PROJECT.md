# Enterprise AI Chat MVP

## What This Is

An enterprise AI chat web application that lets authenticated employees chat with approved LLMs (Alibaba Bailian Qwen and local OpenAI-compatible models) while enforcing input and output safety controls. The MVP is a demo prototype to prove that AI chat can be used safely in an enterprise environment — blocking sensitive content before model calls and blocking unsafe model responses before display.

Primary users are internal employees. Admin users configure models, policies, and view audit metadata.

## Core Value

Prove that employees can use AI chat safely in a controlled enterprise environment — the safety pipeline (input filtering → model call → output filtering) must work reliably and block sensitive or non-compliant content without echoing it.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Employee can sign in through enterprise OIDC authentication (mock OIDC for MVP)
- [ ] Employee can select an allowed model provider (Qwen or local OpenAI-compatible)
- [ ] Employee can send a chat message and receive a streamed response with safety buffering
- [ ] Unsafe or sensitive user input is blocked before any model call, with a safe explanation message
- [ ] Unsafe or sensitive model output is blocked before display, with a safe explanation message
- [ ] Block messages explain the risk category and action taken without echoing sensitive content
- [ ] Employee can browse and resume past conversations (only allowed-through content stored)
- [ ] Audit events are created for allowed and blocked interactions
- [ ] Audit events contain metadata and risk categories but not raw sensitive content
- [ ] Admin can view audit event metadata through a dashboard UI
- [ ] Admin can configure model providers and credentials through a dashboard UI
- [ ] Admin can configure policy thresholds and enabled scanner modules through a dashboard UI
- [ ] Automated tests prove the main allow/block paths

### Out of Scope

- Full model provider marketplace — complex, not core to proving safety pipeline
- Complex multi-provider routing (cost, latency, policy-based) — single model selection sufficient for demo
- Automatic provider fallback — adds complexity without proving safety value
- Local redaction with partial display — MVP blocks full content, no partial content shown
- Custom training or fine-tuning of filtering models — use existing open-source libraries
- Commercial DLP integrations — beyond MVP scope
- Multi-tenant organization management — single enterprise context
- Advanced analytics dashboards — audit viewer sufficient for demo
- Long-term conversation memory using raw prompt storage — only allowed-through content stored
- Fine-grained RBAC beyond employee/admin — two roles sufficient for MVP
- Self-service provider marketplace — admin-only configuration

## Context

- Tech stack: React + TypeScript frontend, Python + FastAPI backend, PostgreSQL database
- Model providers: Alibaba Bailian Qwen (cloud) and local OpenAI-compatible API (self-hosted)
- Safety filtering uses Presidio (PII detection, data classification) and Llama Guard / LLM Guard (jailbreak, prompt injection, harmful content, compliance)
- Both filtering libraries wrapped behind internal interfaces (DataProtectionScanner, LLMGuardrailScanner) so implementations can change
- Authentication starts with mock OIDC that mimics the real OIDC flow; real enterprise IDP adapter swapped in later
- Frontend never calls model providers directly — all model calls and safety checks go through the backend
- Streaming responses with safety buffering: model output streams to users but safety checks run with a buffer to block unsafe content before it's displayed
- Enterprise identity provider not yet determined — OIDC chosen as first integration path, LDAP/SSO as future adapter
- Exact filtering library versions and deployment models need confirmation during implementation planning

## Constraints

- **Tech stack**: React + TypeScript frontend, Python + FastAPI backend, PostgreSQL — proven stack for enterprise web apps
- **Architecture**: Frontend never calls model providers directly — all safety enforcement on backend
- **Safety policy**: Block full content on any policy violation — no redaction or partial display
- **Audit**: Log metadata only — never store raw prompts, raw model outputs, or full PII values
- **Auth**: OIDC integration required — no anonymous access, mock OIDC for MVP
- **Deployment**: Local development first (uvicorn + npm dev + local PostgreSQL) — deployment strategy deferred

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Mock OIDC first | Enterprise IDP not yet determined; mock lets MVP focus on core chat + safety pipeline | — Pending |
| Presidio + Llama Guard for filtering | Enterprise needs reliable detection from day one; homegrown regex won't catch nuanced attacks | — Pending |
| Store only allowed-through conversation content | Database should never contain non-compliant data; blocked content only exists as audit metadata | — Pending |
| Local development deployment | Focus on working MVP first; deployment constraints shouldn't slow development | — Pending |
| Streaming with safety buffer | Non-streaming chat feels slow; streaming with buffered safety checks gives responsive UX while maintaining safety | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-21 after initialization*