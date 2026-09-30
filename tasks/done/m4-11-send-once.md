---
id: m4-11-send-once
milestone: 4
depends_on: []
files:
  - coucou/static/coucou/js/compose.js
tests:
  - tests/browser/test_compose.py
finding: m4-F9
---

### Goal
A double tap on Send posts one moment, not two.

### Context
Read `coucou/static/coucou/js/compose.js` (`handleSubmit`) and `tests/browser/test_compose.py`, and follow `coucou/static/coucou/js/name_form.js` (its `busy` state disables the button while saving).
- Today `handleSubmit` awaits `photo.file.arrayBuffer()` before calling `onSend`, so a second tap during that wait builds a second event with a new id: two moments.
- While a send is being prepared, Send is disabled and a second submit does nothing. Once `onSend` has been called, the form clears and Send works again for the next moment.
- No new strings.
- Test it as a person would: two quick `click()`s on Send with a photo chosen (make a real image with Pillow, as `tests/browser/test_me.py`'s `_photo()` does), then check `window.sent` has exactly one event. Don't dispatch `submit` events by hand: a person can only click.

### Done when
- two quick clicks on Send with a photo post exactly one event
- two quick clicks with only a note post exactly one event
- after a send, the next moment can be sent (a second, separate send works)
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`); run `uv run ruff format tests/browser/test_compose.py` last

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 640
gate_failures: []
tokens: 709471
```
