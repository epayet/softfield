---
id: f38-02-updated-note
milestone: f38-the-refresh-prompt-causes-layout-shifting
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
A page that loaded the new version by itself says so for 15 seconds: "✓ Updated HH:MM" where the "↻ New version" tag hangs, so the owner can tell the page is current.

### Context
The picture to build: `.softfield/cards/f38-mockup/updated-note.html` (Proposed). Why: `.softfield/cards/f38-the-refresh-prompt-causes-layout-shifting.md` (D4).
Read the two `location.reload()` calls under "A new version (f38)" in `factory_dashboard/templates/base.html`, the `.bar-stripe` and `.version-tag` rules in `factory_dashboard/static/dashboard.css`, and `test_a_hidden_page_loads_the_new_version_unless_something_would_be_lost` and `test_a_page_coming_back_loads_the_new_version_at_once` in `tests/factory_dashboard/test_app.py` (the browser tests to follow).
- Just before either of those two reloads, store the time in `sessionStorage` (one key, e.g. `softfield-updated`). A tap on the tag itself stores nothing: the owner asked for that reload, so it needs no note.
- On load, if the key is there and under 60 s old, remove it and add `<span class="version-tag updated" role="status"><span class="arrow">✓</span>Updated <span class="at">HH:MM</span></span>` (the reload's local time, 24 h) inside `.bar-stripe`; remove it after 15 s. If a "↻ New version" tag arrives meanwhile, it takes the place.
- `.version-tag.updated`: the tag's cut-corner plate in `--plate`, `--ink` and a `--rule` border, so it reads as a fact and not as something to press. It's not a link, and nothing animates. `sessionStorage` errors (private mode) are caught and ignored.

### Done when
- in a browser test, a page that reloads through the hidden-page path shows "Updated" and a time in `.bar-stripe`, and it's gone after 15 s (use the page's clock, don't wait)
- a page loaded by hand (no stored key) shows no "Updated" note
- the header's height and the top of `<main>` don't change when the note appears or goes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
