---
id: f42-02-top-bar-steps-aside
milestone: f42-the-space-for-me-to-scroll
difficulty: 3
depends_on: [f17-01-status-dot-and-sign, f42-01-review-page-room]
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
On a phone the top bar slides away while the owner scrolls down and comes back as soon as they scroll up, so a page's own content gets the screen.

### Context
Read the top bar and its script in `factory_dashboard/templates/base.html`, `header.bar` and the "Phone top bar" rules in `factory_dashboard/static/dashboard.css`, and `test_phone_top_bar_is_compact_and_tabs_scroll` in `tests/factory_dashboard/test_app.py`. Why: `.softfield/cards/f42-the-space-for-me-to-scroll.md`.
- Under 640 px only: a scroll down of more than 8 px past the bar's height adds a class to `header.bar` that moves it up out of view (`transform: translateY(-100%)`, a short transition); any scroll up, or a scroll position under the bar's height, removes it. From 640 px nothing changes.
- No transition under `prefers-reduced-motion`: it just hides and shows.
- The bar stays `position: sticky`; the live poll's out-of-band swap of the status must not bring it back or lose the class (it swaps the status inside the bar, not the bar).
- One passive `scroll` listener, beside the existing one; no library.

### Done when
- at 390 × 844 on a page taller than the screen: after scrolling down 400 px the bar is out of view (its bounding box ends at or above 0); after scrolling up 50 px it is fully in view at the top
- at the top of the page it is in view
- at 1024 px scrolling down leaves the bar in view, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 5472
gate_failures: ['stopped', 'stopped']
tokens: 594134
```
