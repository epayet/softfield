---
id: m4-06-me-wiring
milestone: 4
depends_on: [m4-01-compose-note, m4-02-compose-photo, m4-03-thumbnail, m4-04-delivery-list]
files:
  - coucou/static/coucou/js/me.js
tests:
  - tests/browser/test_me.py
---

### Goal
Once named, `me.js` shows `Compose` and `Delivery` in place of the placeholder, and sends through the outbox.

### Context
Read `docs/agents/preact.md`, `coucou/static/coucou/js/me.js`, `coucou/static/coucou/js/outbox.js` (API: D4 in `docs/milestones/m4.md`), `coucou/static/coucou/js/compose.js`, `coucou/static/coucou/js/delivery.js` and `coucou/static/coucou/js/thumbnail.js`. Extend `tests/browser/test_me.py`: its `open_me` fixture opens the real page under the real CSP and stubs `/api/me`; the harness takes `?named=1`, `?spaces=2`, `?lang=fr` (`tests/browser/conftest.py`). Stub `/api/events` with `page.route`. For a photo, copy `set_input_files` from `tests/browser/test_compose.py`.
- Remove the "You're connected!" heading and its "Soon you'll be able…" line. Three existing tests wait for that heading; make them wait for Compose's Send button instead. No new strings in this ticket (the offline line is m4-09).
- After the name is confirmed (or already was): `Compose` with `spaces` from the page data (D2), `Delivery` under it.
- Import `enqueue`, `flush`, `pending`, `retry`, `discard`, `startOutbox` statically from the outbox module (it sits next to me.js, so the specifier is "./outbox.js"); call `startOutbox({onChange, keepRefused: true})` once. `Compose`'s `onSend(event)`: if there's `event.photo`, `thumb = await thumbnail(new Blob([photo.bytes], {type: photo.type}))`; then `enqueue({...event, local: {thumb}})` and `flush()`.
- `onChange` rebuilds `Delivery`'s items from `pending()`: `id`, `status`, `code` pass through, `note` is `payload.note`, `at` is `created_at`, `thumb` is `local.thumb`. Try again → `retry(id)`, Remove → `discard(id)`.
- A sent event leaves `pending()`, so "accepted" means the item disappears from the list.
- Never log note text or photo contents.
- In tests, wait on something that changes: `with page.expect_request("**/api/events"):` around the click, or a `wait_for` on the delivery list. `window.cspViolations` is set at load, so waiting on it returns at once.

### Done when
- sending a note posts one `content.posted` event (JSON) to `/api/events`; while the stub holds the answer the list shows it waiting/sending, and once answered 201 it's gone
- a photo moment is posted as multipart (an `event` part and a `photo` part), and its thumbnail shows in the list while waiting
- a 400 with `code: "note_too_long"` shows "couldn't send" with that reason; Try again re-sends it (a second POST); Remove drops it with no further POST
- the name screen and Disconnect still behave as before; no "You're connected!" remains
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`); lines are at most 100 characters, and `ruff format` won't split a long string for you

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 2469553
logs: var/runs/20260929-142614/m4-06-me-wiring-run3
```
