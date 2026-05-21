# Roadmap: Enterprise AI Chat MVP

## Overview

This roadmap delivers a safety-first enterprise AI chat application in four phases. Starting with authentication foundation, then building the core safety pipeline that blocks unsafe content before model calls and before display, followed by the conversation history and chat interface that users interact with, and finally streaming safety buffering and the admin dashboard for configuration and audit visibility. Each phase delivers a complete, verifiable capability that builds on the previous one.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Auth** - Authentication foundation with mock OIDC and role-based access (completed 2026-05-21)
- [ ] **Phase 2: Safety Pipeline & Chat** - Core safety pipeline, model gateway, non-streaming chat, and automated test coverage
- [ ] **Phase 3: Conversation History & Chat Interface** - Conversation browsing, resuming, and allowed-through content storage
- [ ] **Phase 4: Streaming & Admin Dashboard** - Streaming safety buffer and admin configuration/audit dashboard

## Phase Details

### Phase 1: Foundation & Auth
**Goal**: Employees can securely authenticate and the backend knows their identity and role
**Mode**: mvp
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03
**Success Criteria** (what must be TRUE):
  1. Employee can sign in through mock OIDC authentication and access the application
  2. Backend routes receive authenticated user identity (user ID, role) on every authenticated request
  3. Admin-role users can access admin-only endpoints; employee-role users are restricted to chat endpoints
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — Backend Walking Skeleton: project scaffold, DB schema, mock OIDC auth routes, auth middleware
- [x] 01-02-PLAN.md — Frontend Auth UI: mock OIDC login flow, role selector, Zustand auth store, authenticated home page
- [x] 01-03-PLAN.md — Role-Based Access Enforcement: admin-only endpoint guards, role tests, frontend route guards

### Phase 2: Safety Pipeline & Chat
**Goal**: The safety pipeline reliably blocks unsafe content and employees can chat through it
**Mode**: mvp
**Depends on**: Phase 1
**Requirements**: SAFE-01, SAFE-02, SAFE-03, SAFE-04, SAFE-05, SAFE-06, SAFE-07, SAFE-08, CHAT-01, CHAT-02, TEST-01, TEST-02, TEST-03, TEST-04, TEST-05
**Success Criteria** (what must be TRUE):
  1. Unsafe input is blocked before any model call, with a block message that explains the risk category without echoing sensitive content
  2. Unsafe model output is blocked before display, with a block message that explains the risk category without echoing sensitive content
  3. Scanner failures (crash, timeout, error) block content rather than allowing it unfiltered
  4. Employee can select a model provider and send a chat message that receives a response through the backend
  5. Automated tests prove the main allow, input block, output block, and fail-closed paths work correctly
**Plans**: TBD

### Phase 3: Conversation History & Chat Interface
**Goal**: Employees can browse and resume past conversations through a chat interface, with only allowed-through content stored
**Mode**: mvp
**Depends on**: Phase 2
**Requirements**: HIST-01, HIST-02, HIST-03, HIST-04
**Success Criteria** (what must be TRUE):
  1. Employee can view a list of their past conversations in the chat interface
  2. Employee can resume a past conversation from the conversation list and continue chatting
  3. Database stores only allowed-through message content — blocked content never appears in conversation records
  4. Blocked messages generate audit event entries but no conversation message rows in the database
**Plans**: TBD
**UI hint**: yes

### Phase 4: Streaming & Admin Dashboard
**Goal**: Chat responses stream with safety buffering, and admins can view audit data and manage configuration through a dashboard
**Mode**: mvp
**Depends on**: Phase 3
**Requirements**: CHAT-03, ADMN-01, ADMN-02, ADMN-03
**Success Criteria** (what must be TRUE):
  1. Chat responses stream to the frontend with a safety buffer that prevents unsafe tokens from being displayed before safety checks complete
  2. Admin can view audit event metadata (risk categories, policy actions, timestamps, user and model info) through a dashboard UI
  3. Admin can configure model providers and credentials through a dashboard UI
  4. Admin can configure policy thresholds and enabled scanner modules through a dashboard UI
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Auth | 3/3 | Complete   | 2026-05-21 |
| 2. Safety Pipeline & Chat | 0/? | Not started | - |
| 3. Conversation History & Chat Interface | 0/? | Not started | - |
| 4. Streaming & Admin Dashboard | 0/? | Not started | - |