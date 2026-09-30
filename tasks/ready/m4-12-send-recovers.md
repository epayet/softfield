---
id: m4-12-send-recovers
milestone: 4
depends_on: []
files:
  - coucou/static/coucou/js/compose.js
  - coucou/locale/fr/LC_MESSAGES/djangojs.po
  - coucou/locale/fr/LC_MESSAGES/djangojs.mo
tests:
  - tests/browser/test_compose.py
finding: m4-F9
---

### Goal
If reading the chosen photo fails when Send is pressed, Send works again and the person is told why.

### Context
Read `coucou/static/coucou/js/compose.js` (`handleSubmit`) and `tests/browser/test_compose.py`, and follow `coucou/static/coucou/js/name_form.js` (how it clears `busy`).
- Today `handleSubmit` sets `busy`, then awaits `photo.file.arrayBuffer()`. If that rejects (the file was moved or deleted after it was chosen), `busy` never clears, so Send stays disabled until a reload.
- Clear `busy` whatever happens (`try/finally`). When reading fails: `onSend` isn't called, the note and the photo stay as they were, and the photo's message line (`photoError`, as for "That photo is too big…") says "Couldn't read that photo. Choose it again."
- French, with all its accents and `vous`: "Impossible de lire cette photo. Choisissez-la à nouveau." Add it to `djangojs.po` and compile the `.mo` (see `docs/agents/preact.md`).
- Test it as a person would: choose a photo with `set_input_files` (reuse `_small_image_file()`), make the next read fail once with `page.evaluate("() => { const real = File.prototype.arrayBuffer; File.prototype.arrayBuffer = function () { File.prototype.arrayBuffer = real; return Promise.reject(new Error('gone')); }; }")`, then click Send.

### Done when
- after a failed read, Send is enabled again, `window.sent` is empty, and the note text is still there
- the message "Couldn't read that photo. Choose it again." shows
- choosing the photo again (with reading working) and pressing Send posts exactly one event
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`); run `uv run ruff format tests/browser/test_compose.py` last
