---
name: key-decisions
description: Four key decisions resolved from SPEC.md open questions during initial exploration
metadata:
  type: project
---

# Key Decisions — Enterprise AI Chat MVP

## 1. Authentication: Mock OIDC First
Start with a mock OIDC implementation that mimics the real OIDC flow (login, token, user info). The `current_user` and `oidc` interfaces in `backend/app/auth/` are abstracted so swapping in a real enterprise IDP requires only an adapter change, not route-level surgery.

**Why:** Enterprise identity provider not yet determined; mock lets MVP focus on core chat + safety pipeline.
**How to apply:** Design `oidc.py` as a strategy/adapter pattern. Mock returns a fixed test user with role (employee/admin). When IDP is confirmed, implement real adapter without touching downstream code. See [[oidc-provider-integration]].

## 2. Safety Filtering: Mature Open-Source Library Combination
Use established libraries:
- **Presidio** (Microsoft) for PII detection and data classification
- **Llama Guard** (Meta) or equivalent for jailbreak, prompt injection, harmful content, and compliance checks

Both are Python-native, well-maintained, and enterprise-friendly. Wrap them behind `DataProtectionScanner` and `LLMGuardrailScanner` interfaces so implementations can change without affecting the pipeline.

**Why:** Enterprise needs reliable detection from day one; homegrown regex/keyword filtering won't catch nuanced attacks.
**How to apply:** Research exact versions, licenses, and deployment models before selecting. See [[filter-library-selection]] todo.

## 3. Conversation History: Store Only Allowed-Through Original Text
Store conversation history in PostgreSQL, but only persist content that passed all safety checks. Blocked conversations (input or output) are never stored — only their audit metadata is recorded.

**Why:** Users need to review past conversations; blocking storage of sensitive content ensures the database never contains non-compliant data.
**How to apply:** `Conversation` and `Message` DB models only store `content` after safety pipeline returns `PolicyAction.ALLOW`. Blocked messages get audit event entries but no `Message` row.

## 4. Deployment: Local Development First
MVP runs locally: `uvicorn` for backend, `npm run dev` for frontend, local PostgreSQL. Deployment strategy (Docker Compose, K8s, VM) deferred until MVP is functional.

**Why:** Focus on building a working MVP first; deployment constraints shouldn't slow development.
**How to apply:** Use standard venv + uvicorn + npm dev workflow. No Docker or K8s config needed yet. Environment variables for DB connection and model credentials via `.env` files.