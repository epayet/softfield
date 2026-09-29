---
id: m4-09-me-offline
milestone: 4
depends_on: [m4-06-me-wiring]
files:
  - coucou/static/coucou/js/me.js
  - coucou/locale/fr/LC_MESSAGES/djangojs.po
  - coucou/locale/fr/LC_MESSAGES/djangojs.mo
tests:
  - tests/browser/test_me.py
---

### Goal
The /me/ app shows a quiet line while the device is offline.

### Context
Read `docs/agents/preact.md`, `coucou/static/coucou/js/me.js` and `tests/browser/test_me.py` (its `open_me` fixture and the `/api/events` stub). The outbox already flushes on the `online` event (`coucou/static/coucou/js/outbox.js`, `startOutbox`); this ticket only adds the line.
- Offline is `navigator.onLine === false` at start, then the window's `offline` / `online` events.
- The line: "You're offline. Your moments will go when you're back." Calm, not an error: a plain `<p role="status">`, no alarm styling. French goes in `djangojs.po`, compiled to `djangojs.mo`.
- In tests, `page.context.set_offline(True)` fires `offline` and makes requests fail; `set_offline(False)` fires `online`.

### Done when
- offline at start, or on going offline: the line shows (English and French); back online: it goes
- offline: sending a note queues it as waiting and shows the line; going online delivers it with exactly one POST
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`); lines are at most 100 characters, and `ruff format` won't split a long string for you
