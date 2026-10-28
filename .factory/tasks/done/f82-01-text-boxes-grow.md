---
id: f82-01-text-boxes-grow
milestone: f82-the-plant-idea-text-box-is
agent: developer
difficulty: 2
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
Every text box on the dashboard grows with what is typed in it, up to about 60% of the screen's height, and only then scrolls inside; the Plant box on `/planning` first.

### Context
Read `.factory/cards/f82-the-plant-idea-text-box-is.md` ("What happens today", D1–D3), then the inline `<script>` in `factory_dashboard/templates/base.html`, which every page loads.
- One delegated listener on `document` in that script, beside `liveIdle`: on `input` and on `focusin` of any `textarea`, set its `style.height` to `auto`, then to its `scrollHeight` (plus its borders). Focus covers values set by a script, which fire no `input` event: Try again on a refused note (`factory_dashboard/templates/planning.html`) fills the Plant box and focuses it.
- In `factory_dashboard/static/dashboard.css`, one rule for `textarea`: `max-height: 60vh` and `overflow-y: auto`, so past that it scrolls inside. Leave every `rows=` as it is: it stays the starting and smallest height.
- Boxes drawn again by htmx (the Plant form after a send, a thread's reply) start at their `rows` height: nothing to do for them.
- Follow the Playwright tests of the Plant box in `tests/factory_dashboard/test_planning.py` (`page`, `planning`, `serve` fixtures; `page.fill('#plant textarea[name="text"]', …)`). Use `page.type` or `press_sequentially` where an `input` event must fire line by line.
- The dashboard is English only: no translation needed.

### Done when
- typing ten lines in the Plant box makes it taller than at load, with no scrollbar inside (its `scrollHeight` equals its `clientHeight`)
- typing far past 60% of the window's height stops it at about that height, and it scrolls inside
- emptying the box brings it back to its four-row height, never below
- after a plant is sent, the fresh Plant box is back at its four-row height
- a key point's comment box on a card's thread grows the same way (the rule is page-wide, not the Plant box's)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 2072
gate_failures: ['all-tests', 'stopped']
tokens: 1330591
```
