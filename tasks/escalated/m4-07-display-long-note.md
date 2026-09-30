---
id: m4-07-display-long-note
milestone: 4
depends_on: []
files:
  - coucou/static/coucou/css/display.css
tests:
  - tests/browser/test_display.py
---

### Goal
A 280-character note (the longest a person can now send) fits the display without overflowing, at phone and display sizes.

### Context
`coucou/static/coucou/css/display.css` styles the display page; `#moment-note` uses `font-size: 2.5rem`. `tests/browser/test_display.py` already opens the display against a fake server (`server`, `_open`, `_m`) and `tests/browser/conftest.py` has `layout_problems`, `PHONE` and `DISPLAY`. Today a long note pushes the byline or the reaction buttons off screen. Fix it in plain CSS (wrapping, a smaller size for long text, scrolling as a last resort); no JS.

### Done when
- a browser test shows a 280-character note (with and without a photo) and `layout_problems(page) == []` at `PHONE` and at `DISPLAY`
- a 280-character note with no spaces (one long word) doesn't overflow sideways either
- a short note still looks as before (same font size)
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: BLOCKED: needs-file
attempts: 3
tokens: 4377773
logs: var/runs/20260929-222408/m4-07-display-long-note
```
