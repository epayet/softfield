---
id: f251-02-phone-words-stay-on-screen
milestone: f251-i-want-to-see-computer-uptime
difficulty: 2
depends_on: []
files:
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
On a phone, the status words that a tap on the dot opens (with F251's "Computer on … · since …" line) sit fully on screen: their first letters are no longer cut off at the left edge.

### Context
The owner, 2026-11-17: "The text overflows on the left on mobile I can't see the beginning."
- Cause, in the phone block (max-width 639px) of `factory_dashboard/static/dashboard.css`: `.bar-top.show-words .factory-status .words` is `position: absolute; right: 0`, anchored to `.factory-status`, which sits second in the row, just after the brand. A box wider than the space left of the status's right edge (the uptime line made it wider) grows leftwards past the screen.
- Fix: hang the box from the bar's row instead. In the phone block, `.bar-top` gets `position: relative`, `.factory-status` `position: static`, and the words `left: 4px; right: auto; max-width: calc(100% - 8px)`, wrapping when longer. `.factory-status.asked`'s dashed edge and the wide-screen layout don't change.
- The picture: the phone frame of the Proposed in `.softfield/cards/f251-mockup/uptime.html`.
- Test next to `test_phone_top_bar_is_compact_and_tabs_scroll` in `tests/factory_dashboard/test_app.py` (the `PHONE` viewport, `open_overview`). Give the status long words (a pause by you with a project name, as the owner's "Paused by you since 19:28 · coaster-ranker") and an uptime, tap `.dot-btn`, then measure `.factory-status .words`.

### Done when
- at the phone width, after a tap on the dot, the words box's left edge is at 0 or more and its right edge within the viewport
- a status long enough to pass the screen's width wraps inside the box rather than overflowing
- the page still doesn't scroll sideways, and the wide screen's top bar is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 3600
gate_failures: ['stopped']
tokens: 2464069
```
