---
name: filter-library-selection
description: Research and select the exact open-source filtering libraries for PII detection and content safety
metadata:
  type: todo
  priority: high
---

# Todo: Filter Library Selection Research

## Task
Evaluate and select the concrete open-source filtering libraries for the two scanner interfaces:

### DataProtectionScanner (PII + sensitive data + data classification)
Candidates:
- **Microsoft Presidio** — PII detection + anonymization, Python + REST API, customizable recognizers
- Evaluate: version stability, license (MIT), deployment model, language support, custom recognizer flexibility

### LLMGuardrailScanner (jailbreak, prompt injection, harmful content, compliance)
Candidates:
- **Meta Llama Guard** — classification model for safety categories, available via HuggingFace
- **ProtectAI LLM Guard** — Python library for prompt injection, jailbreak detection, PII
- **NeMo Guardrails** (NVIDIA) — conversational guardrails framework
- Evaluate: which covers the most required categories, Python integration ease, license, inference requirements (local vs API call)

## Acceptance Criteria
- [ ] Selected DataProtectionScanner library confirmed with version, license, and deployment notes
- [ ] Selected LLMGuardrailScanner library confirmed with version, license, and deployment notes
- [ ] Both libraries wrap cleanly behind the interfaces in `backend/app/safety/`
- [ ] License and deployment model compatible with enterprise use