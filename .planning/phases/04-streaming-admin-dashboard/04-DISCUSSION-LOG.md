# Phase 4: Streaming & Admin Dashboard - Discussion Log

**Date:** 2026-05-22
**Areas discussed:** 6

## Streaming Safety Buffer

| Question | Options | Selected |
|----------|---------|----------|
| How should the safety buffer work? | Full accumulation / Sliding window / Stream-then-retract | Sliding window release |
| Window granularity? | Sentence-based / Fixed token count / You decide | Sentence-based chunks |
| Block mid-stream behavior? | Replace all / Append block / Hide partial | Inline redaction (custom: continue streaming, replace sensitive with REDACTED labels) |
| Input vs output policy? | Redact output only / Full block both | Redact output only, keep input full-block |
| Transport mechanism? | SSE / WebSocket | SSE |
| What to store in DB? | Full original / Redacted version / Full + flag | Store full original in DB |
| SSE event format? | Typed events / Uniform chunks | Typed events (chunk/redacted/done) |
| Separate endpoint? | New /chat/stream / Query param / Replace entirely | New /chat/stream endpoint |
| Frontend fallback? | Auto-degrade to non-streaming / Stream only | Auto-degrade to non-streaming |

## Streaming Render Experience

| Question | Options | Selected |
|----------|---------|----------|
| Render method? | Incremental append / Typewriter animation | Incremental append (typing effect) |
| Redacted content UI? | Red label / Gray italic / Icon + tooltip | Red label style |

## Admin Audit Viewer

| Question | Options | Selected |
|----------|---------|----------|
| Layout? | Data table / Stats + table / Timeline | Stats cards + table + filter bar |
| Filter capability? | Multi-dimension combined / Single search | Multi-dimension combined |
| Pagination? | Traditional / Infinite scroll | Traditional pagination |

## Admin Configuration UI

| Question | Options | Selected |
|----------|---------|----------|
| Config storage? | DB / File / Hybrid | DB storage |
| Apply mode? | Save button / Immediate | Save button confirmation |
| Navigation? | Sidebar / Top tabs | Sidebar navigation |
| Model config UI? | Card list + modal / Table + inline edit | Card list + edit modal |
| Policy config UI? | Scanner list + toggle/slider / Detailed form | Scanner list + toggle/slider |
| API Key display? | Masked + encrypted / Status mark + re-input | Masked (****last4) + encrypted storage |

## Admin Route Structure

| Question | Options | Selected |
|----------|---------|----------|
| Route structure? | /admin/* nested / Flat top-level | /admin/* nested routes |

## Audit Statistics

| Question | Options | Selected |
|----------|---------|----------|
| Stats cards? | 3-card today overview / 4-5 cards + trend | 4-5 cards + 7-day trend |
| Time range? | Today/7d/30d toggle / Custom date picker | Today/7d/30d toggle |

## Notes

- User explicitly chose inline redaction over full-block for streaming output — this is a deliberate policy deviation from SAFE-03 for the streaming context only
- Input remains full-block per existing Phase 2 implementation
- Full original stored in DB means admins can see unredacted content if needed
