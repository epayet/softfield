---
id: m4-07-display-long-note
milestone: 4
depends_on: []
files:
  - coucou/static/coucou/css/display.css
tests:
  - tests/browser/test_display_long_note.py
---

### Goal
A 280-character note (the longest a person can now send) fits the display without overflowing, at phone and display sizes.

### Context
`coucou/static/coucou/css/display.css` styles the display page; `#moment-note` uses `font-size: 2.5rem`. Today a long note pushes the byline or the reaction buttons off screen. Fix it in plain CSS (wrapping, a smaller size for long text, scrolling as a last resort); no JS.

`tests/browser/test_display.py` already opens the display against a fake API: the `server` fixture, `_open(page, origin)` and `_m(n, **extra)` (a moment; `_m(3, note="…", photo="/api/media/m3")` gives one with a photo). Set the moments shown with `server["pages"][None] = {"moments": [...], "more": False}` before `_open`. `test_nothing_overlaps_or_leaves_the_screen` there is the shape to copy. `tests/browser/conftest.py` has `layout_problems`, `PHONE` and `DISPLAY`.

`tests/browser/test_display.py` is protected: don't edit it. Write your tests in the new file `tests/browser/test_display_long_note.py` and import what you need, e.g. `from tests.browser.test_display import _m, _open, server  # noqa: F401` (ruff sees the fixture as unused).

### Done when
- a browser test shows a 280-character note (with and without a photo) and `layout_problems(page) == []` at `PHONE` and at `DISPLAY`
- a 280-character note with no spaces (one long word) doesn't overflow sideways either
- a short note still looks as before (same font size)
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
