---
id: f68-02-brand-tests-check-content
finding: f68-01-cp6
milestone: f68-i-want-the-factory-to-be
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/_partials/logo.svg
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The brand's tests check what the owner sees: the light theme's colours on the logo and on "Soft", and a third-party host anywhere on a page.

### Context
Read `test_no_page_or_stylesheet_names_a_third_party_host` and `test_the_logo_follows_the_theme_tokens` in `tests/factory_dashboard/test_app.py`, and the logo in `factory_dashboard/templates/_partials/logo.svg`.
- The third-party-host test now skips a match when `xmlns=` appears anywhere earlier in the page text. The logo is inline in the top bar, so on every page every host after the bar is skipped. Skip only the namespace URL itself (`http://www.w3.org/2000/svg`).
- `test_the_logo_follows_the_theme_tokens` is parametrized on dark and light but only asserts the `svg` is visible: it passes whatever the colours are. Ticket f68-01 asked that in the light theme the sprout and crate use the light tokens' colours and "Soft" is the amber `--warn-ink`, not the hazard yellow.
- The brand link has no test of its 44 px tall target (f68-01 asked for it).

### Done when
- a page that names `https://cdn.example.com/x.js` after the top bar makes the third-party host test fail
- in the light and in the dark theme, the computed `fill` of the logo's crate and the computed `stroke` of its sprout equal the computed `--hazard` and `--good` of that theme, and the two themes differ; "Soft" has the computed colour of `--warn-ink`
- the brand link is at least 44 px tall at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
