---
phase: 3
slug: conversation-history-chat
status: draft
shadcn_initialized: false
preset: none
created: 2026-05-22
---

# Phase 3 — UI Design Contract

> Visual and interaction contract for conversation history sidebar and chat interface layout.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | none (Tailwind utility classes) |
| Icon library | Lucide React |
| Font | System font stack (Tailwind default) |

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, inline padding |
| sm | 8px | Compact element spacing, sidebar item padding-y |
| md | 16px | Default element spacing, sidebar item padding-x |
| lg | 24px | Section padding, chat message padding |
| xl | 32px | Layout gaps |
| 2xl | 48px | Major section breaks |
| 3xl | 64px | Page-level spacing |

Exceptions: none

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 14px | 400 | 1.5 |
| Label | 12px | 500 | 1.4 |
| Heading | 16px | 600 | 1.3 |
| Display | 20px | 600 | 1.2 |

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | white (#ffffff) | Chat area background, message area |
| Secondary (30%) | gray-50 (#f9fafb) | Sidebar background, active conversation highlight uses gray-100 |
| Accent (10%) | blue-600 (#2563eb) | "New conversation" button, active conversation left border indicator |
| Destructive | red-600 (#dc2626) | Destructive actions only |

Accent reserved for: "New conversation" button fill, active conversation left border indicator, send button

---

## Layout Contract

| Element | Spec |
|---------|------|
| Sidebar width | 280px fixed |
| Sidebar collapse | Hidden below 768px breakpoint, toggle via hamburger icon |
| Chat area | flex-1, fills remaining width |
| Overall layout | flex row: sidebar (left) + chat area (right), full viewport height |
| Sidebar item height | auto, padding 8px vertical / 16px horizontal |
| Sidebar divider | 1px border-gray-200 between date groups |
| Title truncation | single line, text-ellipsis overflow-hidden whitespace-nowrap |

---

## Interaction States

| Element | State | Visual |
|---------|-------|--------|
| Sidebar item | default | bg-transparent, text-gray-700 |
| Sidebar item | hover | bg-gray-100 |
| Sidebar item | active (selected) | bg-gray-100, left border 3px blue-600 |
| New conversation button | default | bg-blue-600 text-white, full sidebar width minus padding |
| New conversation button | hover | bg-blue-700 |
| Chat message (user) | — | right-aligned, bg-blue-50, rounded-lg, max-width 80% |
| Chat message (assistant) | — | left-aligned, bg-white border border-gray-200, rounded-lg, max-width 80% |

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | "New conversation" |
| Empty state heading | "No conversations yet" |
| Empty state body | "Start a new conversation to begin chatting with AI." |
| Error state | "Failed to load conversations. Check your connection and try again." |
| Destructive confirmation | not applicable (no delete in MVP per D-UI discretion — deferred) |
| Date group labels | "Today", "Yesterday", "Previous 7 days", then month name (e.g. "May") |
| Loading state | Skeleton placeholder lines in sidebar |

---

## Component Inventory

| Component | Purpose | New/Existing |
|-----------|---------|--------------|
| ConversationSidebar | Left panel with conversation list + new button | New |
| ConversationItem | Single row in sidebar (title + date) | New |
| ConversationDateGroup | Groups items under date heading | New |
| EmptyConversations | Empty state when no conversations exist | New |
| ChatPage | Updated to flex-row layout with sidebar | Existing (modified) |
| ChatMessages | Already exists, no change | Existing |
| ChatInput | Already exists, no change | Existing |
| SidebarToggle | Hamburger button for mobile collapse | New |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| No registries | — | not applicable |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
