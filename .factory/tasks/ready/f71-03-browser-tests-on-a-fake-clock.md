---
id: f71-03-browser-tests-on-a-fake-clock
milestone: f71-i-suspect-we-might-need-to
difficulty: 5
depends_on: [f68-07-fix-cdn-regression-test-calls-helper-only, f114-08-fix-bundled-link-test-accepts, f114-09-fix-notification-tests-do-not, f114-10-fix-fallback-onclick-test-always-passes]
agent: lead
files:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_planning.py
tests_only: true
---

### Goal
The dashboard's browser tests stop waiting on real time: the same checks, on Playwright's fake clock, so the suite's slowest tests take seconds instead of 10–36 s each.

### Context
F71's findings (`.factory/cards/f71-i-suspect-we-might-need-to.md`, "Findings (2026-10-21)"): the 152 browser tests are 6% of the suite and 40% of its time (468 of 1,175 s in one process). On 16 workers the suite takes as long as its slowest tests allow, and those are these:
- They wait on the pages' real 5 s polls (`hx-trigger="every 5s"` in `factory_dashboard/templates/base.html` and `factory_dashboard/templates/overview.html`): `wait_for_*(…, timeout=REFRESH)` with `REFRESH = 12_000` in `tests/factory_dashboard/test_overview.py`, and fixed `page.wait_for_timeout(6_000)` in `test_the_page_notifies_once_per_new_item_and_once_when_all_is_done` (36 s).
- Eight notification tests in `test_app.py` (17.5 s each, from `test_bundled_link_retains_projects_context`) first wait the full 12 s for `localStorage.getItem('notify:coucou') !== null`, which never comes in them, then take their `except` path and call `window._notifyEstablishBaseline()`. Wait for what each test actually needs instead.
- `test_a_page_that_names_cdn_example_com_after_the_top_bar_fails` ran `runner backfill` over this repo's runs to get one page (28 s alone, 72 s on 16 workers) and left its database in `/tmp`: f68-07 rewrites it; check it now uses the `client` fixture.
- Playwright's Python API has `page.clock` (`install()` before `goto`, then `run_for(ms)` or `fast_forward`), which drives `setInterval` and htmx's `every` triggers. Install it in a fixture the browser tests share, in `tests/factory_dashboard/conftest.py`.
- From `docs/backlog.md` (f13-review, F4): two plant tests in `tests/factory_dashboard/test_planning.py` prove "no re-fetch followed" with a fixed `page.wait_for_timeout(300)` (`test_a_failed_post_leaves_textarea_and_coming_as_they_were`, `test_a_stored_plant_empties_the_box_even_when_the_new_form_never_comes`); a late re-fetch would slip past. Have the page record `htmx:afterRequest` in a list and wait for the post's entry.
- **Change no test's meaning:** each test checks what it checked before; only how it waits changes. The code (`factory_dashboard/static/notify.js` and the templates) is right and doesn't change.

### Done when
- no browser test calls `wait_for_timeout` with more than 500 ms, and none waits for a condition it then gives up on
- `uv run pytest --durations=10 tests/factory_dashboard` shows no test over 5 s
- every changed test still fails when the behaviour it checks is broken (try one per file: drop the poll, or the notify call, and see it fail)
- the listed `tests:` pass on 16 workers (`-n 16`) three runs in a row
- all gates pass (see `docs/workflow.md`)
