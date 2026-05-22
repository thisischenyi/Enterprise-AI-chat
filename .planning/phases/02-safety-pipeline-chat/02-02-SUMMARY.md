---
phase: 02-safety-pipeline-chat
plan: 02
subsystem: safety-pipeline
tags: [safety, pipeline, audit, policy]
dependency_graph:
  requires: [02-01]
  provides: [SafetyPipeline, SafetyPolicy, AuditEvent, AuditRepository]
  affects: [02-03, 02-04]
tech_stack:
  added: []
  patterns: [fail-closed-timeout, metadata-only-audit, parallel-scanner-execution]
key_files:
  created:
    - backend/app/db/migrations/versions/002_audit_events.py
  modified:
    - backend/app/safety/pipeline.py
    - backend/app/safety/policy.py
    - backend/app/audit/events.py
    - backend/app/audit/repository.py
    - backend/app/db/schema.py
decisions:
  - "SafetyPipeline uses asyncio.wait_for with 30s timeout wrapping asyncio.gather for all scanners"
  - "AuditRepository.record_event takes PolicyDecision directly — no intermediate DTO"
  - "Scanner failures replaced with None in results list; all-None triggers fail_closed"
metrics:
  duration: "~8 minutes"
  completed: "2026-05-22"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 02 Plan 02: Safety Pipeline Coordination + Audit Summary

**One-liner:** SafetyPipeline coordinates parallel scanner execution with 30s fail-closed timeout; SafetyPolicy aggregates findings into block/allow decisions; AuditRepository records metadata-only events for every decision.

## Tasks Completed

| # | Name | Commit | Key Files |
|---|------|--------|-----------|
| 1 | SafetyPipeline + SafetyPolicy | b8c2c47 | pipeline.py, policy.py |
| 2 | AuditEvent + AuditRepository | 9e7842d | schema.py, events.py, repository.py, 002_audit_events.py |

## Deviations from Plan

None - plan executed exactly as written.

## Key Implementation Details

- **SafetyPipeline._scan()**: asyncio.wait_for wraps asyncio.gather of all scanners. Exceptions per-scanner caught and replaced with None. All-None = fail_closed.
- **SafetyPolicy.evaluate()**: Any has_violations=True finding triggers block. Uses get_block_message for category-specific templates. scanner_findings_summary contains only anonymized metadata (category labels, confidence, scanner names).
- **AuditEvent**: JSON columns for risk_categories and scanner_findings (SQLite TEXT / PostgreSQL JSONB transparent). Indexed for query patterns.
- **AuditRepository**: Takes AsyncSession, flush-only (caller commits). get_audit_repository dependency for FastAPI DI.

## Self-Check: PASSED
