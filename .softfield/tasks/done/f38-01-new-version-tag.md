---
id: f38-01-new-version-tag
milestone: f38-the-refresh-prompt-causes-layout-shifting
difficulty: 3
depends_on: []
files:
  - factory_dashboard/app.py
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
When the dashboard's code changes, the "new version" notice is a small tag on the top bar's hazard stripe instead of a bar above the page, so nothing on the page moves; a page nobody is looking at loads the new version by itself.

### Context
The picture to build: `.softfield/cards/f38-mockup/new-version-tag.html` (Proposed). Why: `.softfield/cards/f38-the-refresh-prompt-causes-layout-shifting.md`.
Read `VERSION_POLL`, `NEW_VERSION` and the `/version` route in `factory_dashboard/app.py`, `{{ version_poll | safe }}` and the `.hazard` stripe in `factory_dashboard/templates/base.html` (and `window.liveIdle` in its script), the `.new-version` and `header.bar` / `.hazard` rules in `factory_dashboard/static/dashboard.css`, and `test_a_page_says_when_a_new_version_is_available` in `tests/factory_dashboard/test_app.py`.
- The poll moves from `<main>` into the header, inside a wrapper around the `.hazard` stripe that is `position: relative`. `NEW_VERSION` becomes a link `<a class="version-tag" href="" role="status" title="A new version of the dashboard is ready: tap to load it">↻ New version</a>`, drawn `position: absolute` over the right end of the stripe, so the header's height doesn't change.
- The tag's look is the mock-up's: hazard yellow (`--hazard`, `--hazard-ink`), display font, uppercase, a cut corner (`clip-path`), about 24 px tall with a hit area of at least 44 px. No animation. Remove the old `.new-version` rule.
- A hidden page loads the new version itself: when the tag is in the page and `document.visibilityState` is `hidden` (at the swap, or on a later `visibilitychange`), call `location.reload()` only if `window.liveIdle()` is true, so unsent text is never lost. A visible page only shows the tag.
- The phone's top bar may slide away on scroll (f42-02): the tag goes with the bar, which is fine.

### Done when
- `/version` with an old `seen` returns the tag (class `version-tag`, the words "New version", a link to the page itself); with the current one it still returns the poller
- a page's poller span sits inside `header.bar`, not in `<main>`
- at 1024 px and at 390 × 844, swapping the tag in leaves the top of `<main>` and the header's height where they were (bounding boxes before and after the swap are equal)
- `.new-version` no longer appears in `dashboard.css`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: BLOCKED: needs-file
attempts: 2
tokens: 6574424
logs: .softfield/var/runs/20261026-225212/f38-01-new-version-tag
```
