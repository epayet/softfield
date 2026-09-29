---
id: m4-06-me-wiring
milestone: 4
depends_on: [m4-01-compose-note, m4-02-compose-photo, m4-03-thumbnail, m4-04-delivery-list]
files:
  - coucou/static/coucou/js/me.js
  - coucou/locale/fr/LC_MESSAGES/djangojs.po
  - coucou/locale/fr/LC_MESSAGES/djangojs.mo
tests:
  - tests/browser/test_me.py
---

### Goal
`me.js` shows the name screen, then `Compose` and `Delivery`, and sends through the outbox.

### Context
Read `docs/agents/preact.md`, `coucou/static/coucou/js/me.js` (the name screen and Disconnect), `coucou/static/coucou/js/outbox.js` (API: D4 in `docs/milestones/m4.md`), `coucou/static/coucou/js/compose.js` and `coucou/static/coucou/js/delivery.js`. Extend `tests/browser/test_me.py`: its `open_me` fixture opens the real page under the real CSP and stubs `/api/me`; the harness page takes `?named=1`, `?spaces=2` and `?lang=fr` (`tests/browser/conftest.py`). Stub `/api/events` with `page.route`.
- After the name is confirmed (or already was), show `Compose` with `spaces` from the page data (D2), and `Delivery` under it.
- Start the outbox with `startOutbox({onChange, keepRefused: true})`. `Compose`'s `onSend` makes the thumbnail when there's a photo (`thumbnail(new Blob([photo.bytes], {type: photo.type}))`, m4-03), then calls `enqueue({...event, local: {thumb}})` and `flush()`.
- `onChange` rebuilds the `Delivery` items from `pending()`: `id`, `status` and `code` pass through, `note` is `payload.note`, `at` is `created_at`, `thumb` is `local.thumb`. Try again → `retry(id)`, Remove → `discard(id)`.
- **A quiet line while offline** (`navigator.onLine === false`, and the `offline` / `online` events): "You're offline. Your moments will go when you're back." Calm, not an error.
- Never log note text or photo contents.

### Done when
- sending a note posts one `content.posted` event to `/api/events` and the delivery list shows it, then no longer as waiting once accepted
- a photo moment is posted as multipart (an `event` part and a `photo` part)
- a 400 with `code: "note_too_long"` shows "couldn't send" with that reason, and Try again re-sends; Remove drops it
- offline: sending queues it as waiting and shows the offline line; going online delivers it (once)
- the name screen and Disconnect still behave as before; the "You're connected!" placeholder is gone (update only the tests that looked for it)
- new strings go through `gettext()` with French in `djangojs.mo`
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
