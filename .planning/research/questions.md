---
name: research-questions
description: Open research questions for the Enterprise AI Chat MVP
metadata:
  type: reference
---

# Research Questions

## Data Classification Categories
- **Question:** Which data classification categories are required for the first enterprise policy version?
- **Context:** Presidio supports custom recognizers and categories, but the enterprise needs to define what labels matter (e.g., Confidential, Internal, Public, Restricted). This affects `DataProtectionScanner` configuration and policy thresholds in `backend/app/safety/policy.py`.
- **Priority:** High — blocks policy configuration and scanner tuning
- **Status:** Open
- **Added:** 2026-05-21