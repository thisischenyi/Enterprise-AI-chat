---
phase: "04"
plan: "03"
subsystem: admin-config
tags: [admin, model-config, policy-config, crud, encryption]
dependency_graph:
  requires: [04-02]
  provides: [admin-model-crud, admin-policy-crud]
  affects: [provider-registry, safety-pipeline]
tech_stack:
  added: [cryptography/Fernet]
  patterns: [repository-pattern, masked-secrets, optimistic-ui]
key_files:
  created:
    - backend/app/admin/models_repo.py
    - backend/app/admin/policy_repo.py
    - backend/alembic/versions/add_model_policy_configs.py
    - frontend/src/features/admin/ModelsPage.tsx
    - frontend/src/features/admin/PolicyPage.tsx
    - frontend/src/features/admin/components/ModelCard.tsx
    - frontend/src/features/admin/components/ModelEditModal.tsx
    - frontend/src/features/admin/components/ScannerRow.tsx
    - frontend/src/features/admin/components/Toast.tsx
    - frontend/src/features/admin/components/ConfirmDialog.tsx
  modified:
    - backend/app/db/schema.py
    - backend/app/api/admin.py
    - frontend/src/routes.tsx
decisions:
  - "Fernet encryption for API keys with ENCRYPTION_KEY env var (fallback to SECRET_KEY for MVP)"
  - "Policy defaults seeded on first access rather than migration"
metrics:
  completed: "2025-05-22"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 04 Plan 03: Admin Model & Policy Config Summary

Model provider CRUD with Fernet-encrypted API key storage and scanner policy configuration UI with toggle/sensitivity controls.

## What Was Built

### Backend
- **ModelConfig + PolicyConfig** SQLAlchemy models added to schema.py
- **ModelConfigRepository**: full CRUD with Fernet encryption, masked key display (last 4 chars)
- **PolicyConfigRepository**: list with auto-seeding defaults, update enabled/sensitivity
- **Admin API endpoints**: GET/POST/PUT/DELETE /admin/models, GET/PUT /admin/policy/{name}
- **Alembic migration** for both tables
- All endpoints protected by get_admin_user dependency
- API keys never returned in full; response uses "api_key_masked" field only

### Frontend
- **ModelsPage**: 2-column grid of ModelCards with add/edit/delete via modal
- **PolicyPage**: ScannerRow list with toggle + 3-level sensitivity (low/medium/high)
- **Components**: ModelCard, ModelEditModal, ScannerRow, Toast, ConfirmDialog
- Routes updated: /admin/models and /admin/policy now render real pages
- Toast "配置已保存" on successful save operations

## Deviations from Plan

None - plan executed exactly as written.

## Threat Mitigations Applied

| Threat | Mitigation |
|--------|-----------|
| T-04-06 (key disclosure) | api_key_encrypted excluded from response; only masked display returned |
| T-04-07 (privilege escalation) | All endpoints behind get_admin_user |
| T-04-08 (policy tampering) | Pydantic validation constrains sensitivity to low/medium/high |

## Self-Check: PASSED
