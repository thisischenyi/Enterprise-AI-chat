---
phase: 4
slug: streaming-admin-dashboard
status: draft
shadcn_initialized: false
preset: none
created: 2026-05-22
---

# Phase 4 — UI Design Contract

> Visual and interaction contract for streaming chat rendering and admin dashboard (audit viewer, model config, policy config).

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
| xs | 4px | Icon gaps, inline padding, redaction tag padding-y |
| sm | 8px | Compact element spacing, table cell padding-y, stat card internal gap |
| md | 16px | Default element spacing, admin sidebar item padding, filter bar gap |
| lg | 24px | Section padding, stat card padding, table container padding |
| xl | 32px | Layout gaps between major sections |
| 2xl | 48px | Page top padding |
| 3xl | 64px | Not used this phase |

Exceptions: none

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body / Label | 14px | 400 | 1.5 |
| Heading | 16px | 600 | 1.3 |
| Display | 20px | 600 | 1.2 |
| Stat value | 28px | 600 | 1.1 |

Labels use 14px at weight 400 (same as body). Differentiate labels from body text via color (text-gray-500 for labels vs text-gray-900 for body) and context, not weight.

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | white (#ffffff) | Admin content area background, table background |
| Secondary (30%) | gray-50 (#f9fafb) | Admin sidebar background, stat card background, table header row |
| Accent (10%) | blue-600 (#2563eb) | Save button, active admin nav item indicator, trend up indicator |
| Destructive | red-600 (#dc2626) | Block count stat highlight, redaction tags, delete/disable destructive actions |
| Warning | amber-500 (#f59e0b) | Block rate stat when > 20%, sensitivity slider high-end |
| Success | green-600 (#16a34a) | Allow action badge, trend positive, enabled toggle |

Accent reserved for: Save button fill, active admin sidebar left border, pagination active page number

---

## Focal Points

| Page | Primary Visual Anchor | Rationale |
|------|----------------------|-----------|
| Audit page | Stat cards row | First element below heading; large stat values (28px) draw the eye immediately |
| Models page | Model card grid | 2-column grid with card elevation is the dominant visual mass |
| Policy page | Scanner toggle list | Repeated toggle pattern creates rhythm as focal anchor |

---

## Layout Contract

| Element | Spec |
|---------|------|
| Admin sidebar width | 220px fixed |
| Admin sidebar | bg-gray-50, border-r border-gray-200, full viewport height |
| Admin content area | flex-1, padding 24px, overflow-y auto |
| Admin overall layout | flex row: admin sidebar (left) + content area (right) |
| Stat cards row | flex row, gap 16px, wrap on mobile, each card flex-1 min-width 180px |
| Stat card | bg-gray-50 border border-gray-200 rounded-lg padding 24px |
| Data table | full width, border border-gray-200 rounded-lg, overflow-x auto |
| Table row height | 44px minimum |
| Filter bar | flex row, gap 16px, items center, margin-bottom 16px |
| Model config cards | grid, 2 columns on desktop, 1 on mobile, gap 16px |
| Edit modal | centered, max-width 480px, backdrop bg-black/50 |

---

## Streaming Render Contract

| Element | Spec |
|---------|------|
| Streaming message bubble | Same as assistant message (left-aligned, bg-white border, rounded-lg) |
| Typing indicator | Blinking cursor character at end of streaming text |
| Redaction tag | Inline span, bg-red-50 text-red-700 border border-red-200 rounded px-2 py-0.5 text-14px font-semibold |
| Redaction labels | `[PII已过滤]`, `[机密信息已过滤]`, `[策略违规已过滤]` |
| Stream complete | Cursor removed, message finalized |
| Stream error | Gray italic text: "连接中断，已切换为非流式模式" |

---

## Interaction States

| Element | State | Visual |
|---------|-------|--------|
| Admin sidebar item | default | text-gray-600, padding 8px 16px |
| Admin sidebar item | hover | bg-gray-100 |
| Admin sidebar item | active | bg-white, left border 3px blue-600, font-weight 600 |
| Stat card | default | bg-gray-50 border-gray-200 |
| Table row | hover | bg-gray-50 |
| Filter dropdown | default | border-gray-300 rounded, h-36px, text-14px |
| Toggle switch | off | bg-gray-300, circle left |
| Toggle switch | on | bg-green-600, circle right |
| Sensitivity slider | low | left position, green indicator |
| Sensitivity slider | medium | center, amber indicator |
| Sensitivity slider | high | right position, red indicator |
| Save button | default | bg-blue-600 text-white px-16px h-36px rounded |
| Save button | hover | bg-blue-700 |
| Save button | disabled | bg-gray-300 text-gray-500 cursor-not-allowed |
| Pagination page | default | text-gray-600 |
| Pagination page | active | bg-blue-600 text-white rounded |
| Model card | default | bg-white border border-gray-200 rounded-lg p-16px |
| Model card | disabled | opacity-50 |
| Modal backdrop | — | bg-black/50, click to close |

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Admin nav: Audit | "审计日志" |
| Admin nav: Models | "模型配置" |
| Admin nav: Policy | "安全策略" |
| Audit page heading | "审计事件" |
| Stat card: total | "今日事件" |
| Stat card: blocks | "今日拦截" |
| Stat card: rate | "拦截率" |
| Stat card: active user | "最活跃用户" |
| Stat card: trend | "7日趋势" |
| Time range: today | "今天" |
| Time range: 7d | "近7天" |
| Time range: 30d | "近30天" |
| Filter: user | "用户" |
| Filter: model | "模型" |
| Filter: action | "动作" |
| Filter: risk | "风险类别" |
| Action badge: allow | "允许" (green) |
| Action badge: block | "拦截" (red) |
| Action badge: fail_closed | "兜底拦截" (amber) |
| Model config heading | "模型供应商配置" |
| Model card CTA | "编辑模型" |
| Add model CTA | "添加模型" |
| Modal: save | "保存配置" |
| Modal: cancel | "放弃修改" |
| API key display | "••••{last4}" |
| API key field label | "API Key（留空则不修改）" |
| Policy config heading | "安全扫描器配置" |
| Policy card CTA | "编辑策略" |
| Scanner toggle label | "启用" |
| Sensitivity label | "敏感度：低 / 中 / 高" |
| Empty audit table | "暂无审计事件" |
| Empty audit body | "当用户发送消息后，审计记录将显示在此处。" |
| Error state | "加载失败，请检查网络连接后重试。" |
| Save success toast | "配置已保存" |
| Save confirmation | not applicable (D-ADM07: save button is the confirmation) |
| Destructive: disable model | "禁用模型": "确认禁用此模型？禁用后用户将无法选择该模型。" |

---

## Component Inventory

| Component | Purpose | New/Existing |
|-----------|---------|--------------|
| AdminLayout | Flex row with admin sidebar + content outlet | New |
| AdminSidebar | Fixed left nav with 3 items (audit/models/policy) | New |
| AuditPage | Stat cards + filter bar + data table | New |
| AuditStatCards | Row of 4-5 stat cards with values | New |
| AuditFilters | Combined filter bar (time range toggle + dropdowns) | New |
| AuditTable | Paginated data table with action badges | New |
| Pagination | Page numbers + prev/next buttons | New |
| ModelConfigPage | Grid of model provider cards | New |
| ModelCard | Card showing model name, endpoint, status | New |
| ModelEditModal | Modal form for editing model provider | New |
| PolicyConfigPage | List of scanners with toggles + sliders | New |
| ScannerRow | Single scanner: name + toggle + sensitivity slider | New |
| SparklineChart | Simple SVG 7-day trend mini-chart | New |
| ActionBadge | Colored badge for allow/block/fail_closed | New |
| RedactedTag | Inline redaction label in streaming messages | New |
| StreamingMessage | Message bubble with incremental append + cursor | New (extends existing ChatMessage) |
| Toast | Temporary success/error notification | New |
| ConfirmDialog | Modal confirmation for destructive actions | New |

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
