---
id: m4-06-me-wiring
milestone: 4
difficulty: 9
depends_on: [m4-01-compose-note, m4-02-compose-photo, m4-03-thumbnail, m4-04-delivery-list]
files:
  - coucou/static/coucou/js/me.js
tests:
  - tests/browser/test_me.py
---

### Goal
Once named, `me.js` shows `Compose` and `Delivery` in place of the placeholder, and sends through the outbox.

### Context
Read `docs/agents/preact.md`, `coucou/static/coucou/js/me.js`, `coucou/static/coucou/js/outbox.js` (API: D4 in `docs/milestones/m4.md`), `coucou/static/coucou/js/compose.js`, `coucou/static/coucou/js/delivery.js` and `coucou/static/coucou/js/thumbnail.js`. Extend `tests/browser/test_me.py`: its `open_me` fixture opens the real page under the real CSP and stubs `/api/me`; the harness takes `?named=1`, `?spaces=2`, `?lang=fr` (`tests/browser/conftest.py`). Stub `/api/events` with `page.route`. For a photo, copy `_small_image_file()` and `set_input_files` from `tests/browser/test_compose.py`.
- Remove the "You're connected!" heading and its "Soon you'll be able…" line. No new strings in this ticket (the offline line is m4-09).
- Four existing tests depend on that heading. Three wait for it: make them wait for Compose's Send button instead. The fourth, `test_disconnect_asks_then_cancel_goes_back`, reads `#app h1` before and after Cancel; after this ticket the named screen has no `h1`, so compare something both screens have, such as whether the name field or the Send button is visible. Keep its two cases (`""` and `"named=1"`) and don't add branches to it.
- After the name is confirmed (or already was): `Compose` with `spaces` from the page data (D2), `Delivery` under it.
- Import `enqueue`, `flush`, `pending`, `retry`, `discard`, `startOutbox` statically from the outbox module (it sits next to me.js, so the specifier is "./outbox.js"); call `startOutbox({onChange, keepRefused: true})` once. A component's body runs on every render, so a call placed directly in `App` runs many times. `Compose`'s `onSend(event)`: if there's `event.photo`, `thumb = await thumbnail(new Blob([photo.bytes], {type: photo.type}))`; then `enqueue({...event, local: {thumb}})` and `flush()`.
- `onChange` rebuilds `Delivery`'s items from `pending()`: `id`, `status`, `code` pass through, `note` is `payload.note`, `at` is `created_at`, `thumb` is `local.thumb`. Try again → `retry(id)`, Remove → `discard(id)`. `onSent` isn't needed.
- A sent event leaves `pending()`, so "accepted" means the item disappears from the list.
- Never log note text or photo contents.
- Test on the real `/me/` page only (`open_me("named=1")`); don't `mount` a separate `Compose`, it isn't wired to the outbox.
- To see "waiting/sending", hold the answer: a sync `page.route` handler that appends `route` to a list and returns without fulfilling keeps the request open; later the test calls `held[0].fulfill(status=201, json={})`. The list shows the item until then.
- `Compose` refuses a note over 280 characters before it reaches the outbox, so the `note_too_long` stub answers 400 to any note; the note's text doesn't matter. Its text in the list is `CODES.note_too_long` in `coucou/static/coucou/js/delivery.js`.
- Count POSTs in the stub. For Remove: after the refusal, click Remove, wait for the list to be empty, then assert the count didn't grow. No `if … is_visible()` branches in tests: a test that skips a step when it's missing passes without testing.
- In tests, wait on something that changes: `with page.expect_request("**/api/events"):` around the click, or a `wait_for` on the delivery list. `window.cspViolations` is set at load, so waiting on it returns at once.
- Formatting: the gate runs `ruff format --check`, which also joins lines you split by hand when they fit in 100 characters. Two earlier attempts failed only on that. Run `uv run ruff format tests/browser/test_me.py` after your last edit.

### Done when
- sending a note posts one `content.posted` event (JSON) to `/api/events`; while the stub holds the answer the list shows it waiting/sending, and once answered 201 it's gone
- a photo moment is posted as multipart (an `event` part and a `photo` part), and its thumbnail shows in the list while waiting
- a 400 with `code: "note_too_long"` shows "couldn't send" with that reason; Try again re-sends it (a second POST); Remove drops it with no further POST
- the name screen and Disconnect still behave as before; no "You're connected!" remains
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`); run `uv run ruff format` on the files you changed before you finish

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 4224
gate_failures: ['task-tests']
tokens: 3906765
```
