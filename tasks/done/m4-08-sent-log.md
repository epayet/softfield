---
id: m4-08-sent-log
milestone: 4
difficulty: 7
depends_on: [m4-06-me-wiring]
files:
  - coucou/static/coucou/js/me.js
  - coucou/static/coucou/js/sent_log.js
  - coucou/locale/fr/LC_MESSAGES/djangojs.po
  - coucou/locale/fr/LC_MESSAGES/djangojs.mo
tests:
  - tests/browser/test_sent_log.py
  - tests/browser/test_me.py
---

### Goal
Keep the last 10 delivered moments on the device and show them in the delivery list.

### Context
Stretch ticket. Decision D8 in `docs/milestones/m4.md`: `localStorage` key `coucou-sent`, a list of `{id, note, thumb, at}`, newest first, capped at 10. A small module `coucou/static/coucou/js/sent_log.js` (`load()`, `add(entry)`) does the storage; `coucou/static/coucou/js/me.js` adds an entry in the outbox's `onSent(item)` (D4: `startOutbox({onSent})`), as `{id, note: payload.note, thumb: local.thumb, at: created_at}`, and passes the log to `Delivery` (`coucou/static/coucou/js/delivery.js`) as items with `status: "sent"`. The thumbnail is already in `local.thumb` (m4-06).
- Storage can throw (private mode, full): never break sending because of it; drop the oldest on a quota error.
- Never store photo bytes, only the small thumbnail.

### Done when
- a delivered moment appears as sent ✓ and is still there after a reload
- the 11th delivered moment drops the oldest
- a moment is never listed twice (same id)
- a broken `localStorage` (throws) leaves sending working
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1859
gate_failures: []
tokens: 3325641
```
