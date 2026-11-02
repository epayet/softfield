---
id: f68-09-logo-as-designed
milestone: f68-i-want-the-factory-to-be
difficulty: 1
agent: lead
depends_on: []
files:
  - factory_dashboard/templates/_partials/logo.svg
  - factory_dashboard/static/softfield.svg
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The top bar's logo and the browser tab's icon are logo A exactly as the owner chose it in the mock-up, not the redrawn version f68-01 built.

### Context
The picture: `<symbol id="logo-a">` in `.softfield/cards/f68-mockup/logos.html`. f68-01 (a developer) drew its own version in `factory_dashboard/templates/_partials/logo.svg` and `factory_dashboard/static/softfield.svg`: upright slats instead of the two flat planks, thin curled lines instead of the two filled leaves, and a smaller sprout. The owner noticed (2026-10-28).
- Copy the symbol's five shapes as they are, on its `viewBox="0 0 64 64"`, into both files: the partial on the tokens (`--good`, `--hazard`, `--hazard-ink`, through the `.sprout` and `.crate` classes in `factory_dashboard/static/dashboard.css`, whose rules gain a leaf `fill`), the favicon with the dark theme's fixed colours (`#5fd17a`, `#f2b10a`, `#1a1405`). Keep the partial's `aria-hidden="true"`.
- The brand's sizes (28 px, 24 px on a phone) stay; only the drawing changes.

### Done when
- both files hold the mock-up's two leaf paths (`M31 25C21 25 14 19 13 9C23 9 31 14 31 25Z` and `M33 21C42 21 49 15 51 6C41 6 33 11 33 21Z`), filled, and its crate with two flat planks (`M11 40.5H53M11 49.5H53`); no upright slat lines remain
- in a browser, the leaves' fill is the `--good` colour in both themes, and the crate's is `--hazard`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
