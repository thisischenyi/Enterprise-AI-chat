# Enterprise AI Chat MVP

## What This Is

An enterprise AI chat web application that lets authenticated employees chat with approved LLMs (Alibaba Bailian Qwen and local OpenAI-compatible models) while enforcing input and output safety controls. The MVP proves that AI chat can be used safely in an enterprise environment — blocking sensitive content before model calls and blocking unsafe model responses before display, with bilingual (Chinese + English) detection and Chinese-language block messages.

Primary users are internal employees. Admin users configure models, policies, and view audit metadata.

## Core Value

Prove that employees can use AI chat safely in a controlled enterprise environment — the safety pipeline (input filtering → model call → output filtering) must work reliably and block sensitive or non-compliant content without echoing it.

## Requirements

### Validated

- ✓ Employee OIDC authentication (mock OIDC) — v1.0
- ✓ Role-based access (employee/admin) — v1.0
- ✓ Model provider selection (Qwen + OpenAI-compatible) — v1.0
- ✓ Streaming chat with safety buffer — v1.0
- ✓ Input safety filtering (PII, injection, harmful, compliance) — v1.0
- ✓ Output safety filtering before display — v1.0
- ✓ Full-content block with category-specific Chinese messages — v1.0
- ✓ Audit metadata-only logging — v1.0
- ✓ Fail-closed scanner semantics — v1.0
- ✓ Custom Presidio recognizers (Chinese national ID, employee ID, project code, income) — v1.0
- ✓ Conversation history browse/resume — v1.0
- ✓ Only allowed-through content stored — v1.0
- ✓ Admin audit viewer dashboard — v1.0
- ✓ Admin model provider config (DB-first, encrypted API keys) — v1.0
- ✓ Admin policy/scanner config — v1.0
- ✓ Automated tests for allow/block/fail-closed paths — v1.0

### Active

- [ ] Conversation delete functionality (frontend + backend)
- [ ] Real OIDC integration when enterprise IDP confirmed
- [ ] Llama Guard 3 model-based guardrails as inference server
- [ ] Streaming buffer threshold tuning (latency vs safety)

### Out of Scope

- Full model provider marketplace — complex, not core to proving safety pipeline
- Multi-provider routing (cost, latency, policy-based) — single model selection sufficient for demo
- Automatic provider fallback — adds complexity without proving safety value
- Local redaction with partial display — MVP blocks full content, no partial content shown
- Custom training or fine-tuning of filtering models — use existing open-source models
- Commercial DLP integrations — beyond MVP scope
- Multi-tenant organization management — single enterprise context
- Advanced analytics dashboards — audit viewer sufficient for demo
- Raw prompt/output storage — database and logs must never contain sensitive content
- Fine-grained RBAC beyond employee/admin — two roles sufficient for MVP

## Context

- Shipped v1.0 with ~4,500 LOC Python + ~3,000 LOC TypeScript
- Tech stack: React 19 + TypeScript + Vite, Python 3.12 + FastAPI, SQLite WAL (aiosqlite), SQLAlchemy 2 async ORM
- Safety: Presidio (regex-only PII detection, score ≥ 0.7) + Qwen3Guard-Gen-0.6B (generative guard model, Chinese + English) + 33 bilingual regex rules
- Auth: Mock OIDC with session-based tokens (itsdangerous), role-based access (employee/admin)
- Admin: DB-first model config with Fernet-encrypted API keys, policy scanner toggle, audit event viewer
- Streaming: SentenceBuffer (regex sentence splitting) + per-sentence output scan + SSE events
- Database: SQLite WAL mode for MVP, PostgreSQL for production (same SQLAlchemy ORM, easy migration)
- Pushed to GitHub: https://github.com/thisischenyi/Enterprise-AI-chat.git

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Mock OIDC first | Enterprise IDP not yet determined; mock lets MVP focus on core | ✓ Good — adapter pattern ready for real IDP |
| Qwen3Guard-Gen-0.6B over LLM Guard toxicity | LLM Guard toxicity useless for Chinese; Qwen3Guard is generative with bilingual support | ✓ Good — effective bilingual detection |
| DB-first ProviderRegistry | Admin config changes take effect without restart | ✓ Good — immediate propagation |
| SQLite WAL for MVP | Proven at 100-user scale, PostgreSQL migration path clear | ✓ Good — MVP works |
| Presidio regex-only entities | NLP recognizers cause Chinese false positives; regex matches reliable | ✓ Good — zero Chinese false positives |
| SentenceBuffer (full-response-first) | Simpler than per-chunk streaming, reliable safety guarantee | ✓ Good — works well for MVP |
| Chinese block message templates | Never echo content, bilingual support required by enterprise users | ✓ Good — compliant, no echoing |

## Constraints

- **Tech stack**: React + TypeScript frontend, Python + FastAPI backend, SQLite for MVP / PostgreSQL for production
- **Architecture**: Frontend never calls model providers directly — all safety enforcement on backend
- **Safety policy**: Block full content on any policy violation — no redaction or partial display
- **Audit**: Log metadata only — never store raw prompts, raw model outputs, or full PII values
- **Auth**: OIDC integration required — no anonymous access, mock OIDC for MVP
- **Deployment**: Local development first (uvicorn + npm dev + local SQLite) — deployment strategy deferred

---
*Last updated: 2026-05-23 after v1.0 milestone*