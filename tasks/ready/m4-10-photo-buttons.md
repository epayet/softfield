---
id: m4-10-photo-buttons
milestone: 4
depends_on: []
files:
  - coucou/static/coucou/css/me.css
tests:
  - tests/browser/test_me.py
finding: m4-F5
---

### Goal
On `/me/`, only the two photo buttons show ("Take a photo", "Choose a photo"): the browser's own file inputs, with their English "Choose File / No file chosen", don't.

### Context
Read `coucou/static/coucou/js/compose.js` (the `#photo-actions` block: each `input[type=file]` is followed by its `<label for=…>`, which is styled as the button) and `coucou/static/coucou/css/me.css`. CSS only; don't change the markup.
- Hide the inputs visually but keep them usable: the usual "visually hidden" pattern (1 px, clipped, `position: absolute`), not `display: none`, because some iPhone browsers ignore a click on a label whose input isn't rendered.
- A keyboard user must still see where they are: when an input has focus, its label shows a focus outline (`input:focus-visible + label`).
- The labels keep their current look and their 44 px minimum height.
- Tests: extend `tests/browser/test_me.py` using its `open_me("named=1")` fixture. Clicking a label must still open the file chooser: `with page.expect_file_chooser(): page.get_by_text("Choose a photo").click()`.

### Done when
- each file input's box is at most 1×1 px, while its label is at least 44 px high and visible
- clicking "Take a photo" and "Choose a photo" still opens a file chooser (`expect_file_chooser`)
- tabbing to an input gives its label a visible outline (a non-`none` `outline-style` on the label)
- `layout_problems(page) == []` at `PHONE`
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`); run `uv run ruff format tests/browser/test_me.py` last
