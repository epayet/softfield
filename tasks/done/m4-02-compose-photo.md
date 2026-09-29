---
id: m4-02-compose-photo
milestone: 4
depends_on: [m4-01-compose-note]
files:
  - coucou/static/coucou/js/compose.js
  - coucou/locale/fr/LC_MESSAGES/djangojs.po
  - coucou/locale/fr/LC_MESSAGES/djangojs.mo
tests:
  - tests/browser/test_compose.py
---

### Goal
Add the photo to `Compose`: take or choose one, preview it, remove it, send it.

### Context
Extend `coucou/static/coucou/js/compose.js` (from m4-01) and its `tests/browser/test_compose.py`; add to that file, don't create another. Decisions D3 and D7 in `docs/milestones/m4.md` apply.
- Two buttons: "Take a photo" (a file input with `capture`) and "Choose a photo" (a file input without it), both `accept="image/*"`.
- The preview uses an object URL (revoke it when the photo is removed or sent). "Remove the photo" clears it.
- Checks before queueing: type starts with `image/`, size at most `40 * 1024 * 1024` bytes. Otherwise a warm message, and no photo is kept.
- On Send, **read the bytes first** (`await file.arrayBuffer()`; iOS can lose access to the file later), then call `onSend` with `photo: {bytes, type}` beside `payload`. A photo alone (no note) is a valid moment.
- Tests can use small generated files with `set_input_files`; a 40 MB + 1 byte file can be built in the test.

### Done when
- choosing a photo shows a preview; removing it hides it and revokes the URL
- a photo alone sends, with `photo.bytes` an `ArrayBuffer` of the file's size and `photo.type` its type, and no `note` key
- a photo and a note send together
- a file of exactly 40 MB is accepted; 40 MB + 1 byte and a non-image (e.g. `text/plain`) are refused with a message
- the "Take a photo" input has `capture`, the other doesn't
- new strings go through `gettext()`, with warm French (all accents) compiled into `djangojs.mo`
- `layout_problems(page) == []` at `PHONE` with a photo previewed
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 922
gate_failures: []
tokens: 1117930
```
