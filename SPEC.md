# Spec: Enterprise AI Chat MVP

## Objective
Build an internal enterprise AI chat MVP that lets authenticated employees chat with approved LLMs while enforcing input and output safety controls.

The MVP is not a generic ChatGPT clone. Its purpose is to prove that employees can use AI chat in a controlled enterprise environment with:

- Alibaba Bailian Qwen model support.
- Local LLM support through an OpenAI-compatible API.
- Input filtering before model calls.
- Output filtering before responses are shown to users.
- Blocking and user-facing safety prompts when sensitive or non-compliant content is detected.
- Audit logging of metadata and policy decisions without storing raw sensitive content.

Primary users are internal employees. Admin features exist only where needed to configure models, policies, and audit visibility.

## Assumptions
- This is a web application MVP, not a native desktop or mobile app.
- The application has a backend service that owns authentication, policy enforcement, model credentials, audit logging, and model invocation.
- The frontend never calls model providers directly.
- Local LLMs expose an OpenAI-compatible API endpoint.
- Enterprise identity is provided by OIDC first, with LDAP/SSO integration treated as a later adapter if needed.
- Filtering uses open-source third-party components where practical, wrapped behind internal interfaces so implementations can change.
- The MVP blocks sensitive or non-compliant input/output instead of redacting and allowing partial content through.

## Tech Stack
Proposed default stack for the MVP:

- Frontend: React + TypeScript.
- Backend: Python + FastAPI.
- Database: PostgreSQL.
- Cache/session support: Redis if needed after implementation starts.
- Auth: OIDC integration with enterprise identity provider.
- Model adapters:
  - `QwenProvider` for Alibaba Bailian Qwen.
  - `OpenAICompatibleProvider` for local LLM deployments.
- Filtering adapters:
  - `DataProtectionScanner` for PII, sensitive data, and data classification.
  - `LLMGuardrailScanner` for jailbreak, prompt injection, harmful content, and compliance policy checks.

Final open-source filtering libraries must be selected during implementation planning after checking license, language/runtime fit, deployment model, and enterprise policy needs.

## Commands
The repository is currently empty, so these are target commands for the initial scaffold:

```powershell
# Backend
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
ruff check .

# Frontend
cd frontend
npm install
npm run dev
npm run build
npm test
npm run lint
```

## Project Structure
Target structure:

```text
backend/
  app/
    main.py
    api/
      chat.py
      auth.py
      admin.py
    auth/
      oidc.py
      current_user.py
    models/
      providers.py
      qwen.py
      openai_compatible.py
    safety/
      pipeline.py
      data_protection.py
      llm_guardrails.py
      policy.py
    audit/
      events.py
      repository.py
    db/
      schema.py
      migrations/
    tests/
frontend/
  src/
    app/
    components/
    features/
      chat/
      auth/
      admin/
    lib/
    tests/
docs/
  architecture.md
  security-policy.md
SPEC.md
```

## Core Flow
1. User authenticates through enterprise identity.
2. User selects an allowed model target: Alibaba Bailian Qwen or local OpenAI-compatible LLM.
3. User submits a chat message.
4. Backend runs input safety checks:
   - Data classification.
   - PII detection.
   - Sensitive business data detection.
   - Prompt injection and jailbreak detection.
   - Harmful or non-compliant request classification.
5. If input violates policy, backend blocks the request, records audit metadata, and returns a safe user prompt without echoing sensitive text.
6. If input passes, backend calls the selected model provider.
7. Backend runs output safety checks on the model response.
8. If output violates policy, backend blocks the response, records audit metadata, and returns a safe user prompt without showing the unsafe response.
9. If output passes, backend returns the response to the user.

## Safety Policy
Input and output are both filtered. Detection must cover:

- PII and personal data.
- Sensitive enterprise data.
- Data classification labels or inferred classification categories.
- Compliance-restricted content.
- Prompt injection.
- Jailbreak attempts.
- Harmful content.
- Model responses that reveal sensitive data or violate policy.

Default action for any policy violation:

- Block the full input or output.
- Show a short explanation with the risk category and action taken.
- Do not echo the detected sensitive content.
- Write an audit event with metadata only.

Example blocked input message:

```text
Your message was blocked because it appears to contain sensitive personal or business information. Remove the sensitive content and try again.
```

Example blocked output message:

```text
The AI response was blocked because it may violate company safety or compliance policy. Try rephrasing your request or contact an administrator if this seems incorrect.
```

## Audit Logging
Audit logs must include:

- Event ID.
- Timestamp.
- User ID.
- User department or group if available.
- Session ID.
- Conversation ID.
- Selected model provider.
- Selected model name or deployment ID.
- Direction: input or output.
- Risk categories detected.
- Policy action: allowed or blocked.
- Scanner names and versions when available.
- Request correlation ID.

Audit logs must not include:

- Raw user prompt text.
- Raw model output text.
- Full PII values.
- Secrets, API keys, tokens, or provider credentials.

Optional safe fields:

- Short normalized reason codes.
- Count of detected items by category.
- Hashes of canonicalized content only if explicitly approved later.

## Authentication And Authorization
The MVP must not allow anonymous use.

Required:

- Enterprise login through OIDC or another approved identity integration.
- User identity available to backend routes.
- Audit events linked to authenticated users.
- Role distinction between employee and admin.

Admin MVP capabilities:

- View audit event metadata.
- Configure allowed model providers.
- Configure provider credentials through backend-only secure storage.
- Configure policy thresholds or enabled scanner modules.

Out of scope for MVP:

- Fine-grained RBAC beyond employee/admin.
- Full multi-tenant organization management.
- Self-service provider marketplace.

## Model Provider Requirements
Model providers must be accessed through a backend interface.

Provider interface must support:

- Provider ID.
- Model or deployment ID.
- Chat completion request.
- Timeout handling.
- Error normalization.
- Optional streaming later, but streaming is not required for MVP.

MVP providers:

- Alibaba Bailian Qwen.
- Local OpenAI-compatible API.

Out of scope:

- Full provider marketplace.
- Complex routing by cost, latency, or policy.
- Automatic fallback across providers.
- User-supplied provider credentials.

## Code Style
Backend example:

```python
from dataclasses import dataclass
from enum import Enum


class PolicyAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"


@dataclass(frozen=True)
class SafetyFinding:
    category: str
    severity: str
    source: str


@dataclass(frozen=True)
class SafetyDecision:
    action: PolicyAction
    findings: list[SafetyFinding]


def should_block(decision: SafetyDecision) -> bool:
    return decision.action == PolicyAction.BLOCK
```

Frontend conventions:

- Use TypeScript for all application code.
- Keep API clients in `frontend/src/lib`.
- Keep chat-specific components under `frontend/src/features/chat`.
- Do not expose provider API keys or safety policy internals to the browser.

Backend conventions:

- Keep provider integrations behind interfaces in `backend/app/models`.
- Keep filtering integrations behind interfaces in `backend/app/safety`.
- Keep audit writes centralized in `backend/app/audit`.
- Do not pass raw sensitive content into logs.

## Testing Strategy
Required test levels:

- Unit tests for policy decisions, provider adapters, audit event construction, and safety pipeline behavior.
- Integration tests for chat flow:
  - Allowed input returns model output.
  - Blocked input does not call model provider.
  - Blocked output does not return raw model output.
  - Audit metadata is recorded for allow and block decisions.
- Auth tests for protected routes.
- Frontend tests for chat state, blocked-message display, and model selection.

Security-focused test fixtures must include:

- PII-like values.
- Sensitive business data examples.
- Prompt injection attempts.
- Jailbreak-style requests.
- Harmful content requests.
- Model output containing disallowed content.

Tests must assert that blocked responses do not echo sensitive input or unsafe output.

## Boundaries
Always:

- Authenticate users before chat access.
- Run input filtering before every model call.
- Run output filtering before showing every model response.
- Block full content on policy violation.
- Record audit metadata for allow and block decisions.
- Keep model credentials on the backend only.
- Avoid raw sensitive content in application logs and audit logs.

Ask first:

- Adding a new model provider.
- Changing the block-by-default policy.
- Storing prompt or response content.
- Adding content hashing to audit logs.
- Adding a new third-party filtering library.
- Introducing streaming responses.
- Changing authentication provider assumptions.

Never:

- Allow anonymous chat access.
- Send detected sensitive content back in the block prompt.
- Store API keys in frontend code.
- Log raw prompts, raw model outputs, or full PII values.
- Bypass safety checks for a model provider.
- Remove or weaken safety tests to make a build pass.

## Success Criteria
The MVP is successful when:

- An employee can sign in through enterprise identity.
- An employee can select Alibaba Bailian Qwen or a local OpenAI-compatible LLM.
- A safe prompt can be submitted and answered.
- Unsafe or sensitive user input is blocked before any model call.
- Unsafe or sensitive model output is blocked before display.
- Block messages explain the category and action without echoing sensitive content.
- Audit events are created for allowed and blocked interactions.
- Audit events contain metadata and risk categories but not raw sensitive content.
- Admin users can configure the enabled model endpoints and view audit metadata.
- Automated tests prove the main allow/block paths.

## Out Of Scope
- Full model provider marketplace.
- Complex multi-provider routing.
- Cost optimization and automatic fallback.
- Local redaction with partial display.
- Custom training or fine-tuning of filtering models.
- Commercial DLP integrations.
- Multi-tenant organization management.
- Advanced analytics dashboards.
- Long-term conversation memory using raw prompt storage.

## Open Questions
- Which enterprise identity provider should be used first: OIDC, LDAP, SAML, or another existing SSO path?
- Which exact open-source filtering libraries should be selected after license and deployment review?
- Which data classification categories are required for the first enterprise policy version?
- Should chat conversation history be stored at all, and if yes, should it exclude blocked content and sensitive content?
- Is streaming required for the first demo, or should all responses be buffered until output filtering completes?
- What deployment target should the MVP assume: internal VM, Docker Compose, Kubernetes, or existing platform?
