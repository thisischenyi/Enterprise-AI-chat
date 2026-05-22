# Phase 3: Discussion Log

**Phase:** 03-conversation-history-chat
**Date:** 2026-05-22
**Mode:** default (all areas selected)

## Areas Discussed

### 1. Conversation Data Model
- **Options presented:** Auto-title from first message / User-editable title / No title (date only)
- **Selected:** Auto-title from first message
- **Options presented:** Include chat history in model calls / Stateless (no history)
- **Selected:** Include chat history in model calls

### 2. Conversation List UI
- **Options presented:** Sidebar on chat page / Separate conversations page
- **Selected:** Sidebar on chat page
- **Options presented:** Title + date / Title + date + preview snippet
- **Selected:** Title + date

### 3. Storage Boundary Enforcement
- **Options presented:** API-level gate / DB-level enforcement
- **Selected:** API-level gate
- **Options presented:** Lazy creation (only on first allowed message) / Eager creation
- **Selected:** Lazy creation

### 4. Resume Conversation Behavior
- **Options presented:** Full history / Paginated (last 50)
- **Selected:** Full history (MVP)
- **Options presented:** Last 20 messages context / Last 10 messages context
- **Selected:** Last 20 messages

## Deferred Ideas
- Message search/filtering
- Conversation sharing
- Export conversation
- Folders/tags/pinning
