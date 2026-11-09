---
id: f71-03-browser-tests-on-a-fake-clock
milestone: f71-i-suspect-we-might-need-to
difficulty: 5
depends_on: [f71-04-test-gates-on-workers]
agent: lead
files:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_coming.py
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_proposal.py
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_coming.py
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_proposal.py
  - tests/factory_dashboard/test_board.py
tests_only: true
---

### Goal
The dashboard's browser tests stop waiting on real time: the same checks, on Playwright's fake clock, so the suite's slowest tests take seconds instead of 10–36 s each.

### Context
Read `.softfield/cards/f71-i-suspect-we-might-need-to.md` ("Findings (2026-10-21)", "What we saw on 2026-11-05", D10). On workers, the suite takes as long as its slowest tests allow.
- **Measure first, on main:** `uv run pytest --durations=30 -n 16` over `tests/runner` and `tests/factory_dashboard`. Start with the tests it names, whatever their cause, including any in `tests/runner` that this ticket's files don't list (say so in your final note; they become a follow-up).
- They wait on the pages' real 5 s polls (`hx-trigger="every 5s"` in `factory_dashboard/templates/base.html`): `timeout=REFRESH` and `LIVE` in `tests/factory_dashboard/test_app.py`, `tests/factory_dashboard/test_overview.py`, `tests/factory_dashboard/test_planning.py`, `tests/factory_dashboard/test_thread.py` and `tests/factory_dashboard/test_proposal.py`, and fixed `page.wait_for_timeout(6_000)` (nine in `tests/factory_dashboard/test_app.py`, one in `tests/factory_dashboard/test_overview.py`).
- The pattern to follow is `refresh` in `tests/factory_dashboard/test_line.py`: `page.clock.install()` before the page opens, `page.clock.run_for(5100)`, then wait for the redraw itself. Share it in `tests/factory_dashboard/conftest.py`.
- "Nothing happened" checks (`wait_for_timeout` then an assert on what wasn't shown) run a poll on the fake clock and wait for that poll's response before asserting.
- `tests/factory_dashboard/test_coming.py`: `test_a_failed_post_leaves_textarea_and_coming_as_they_were` and `test_a_stored_plant_empties_the_box_even_when_the_new_form_never_comes` prove "no re-fetch followed" with `page.wait_for_timeout(300)`, and a late re-fetch would slip past. Have the page record `htmx:afterRequest` in a list and wait for the post's entry.
- **Change no test's meaning:** each test checks what it checked before; only how it waits changes. The code (`factory_dashboard/static/notify.js` and the templates) is right and doesn't change.

### Done when
- no browser test calls `wait_for_timeout` with more than 500 ms, and none waits for a condition it then gives up on
- `uv run pytest --durations=10 tests/factory_dashboard` shows no test over 5 s, or your final note names each one left and why
- every changed test still fails when the behaviour it checks is broken (try one per file: drop the poll, or the notify call, and see it fail)
- the listed `tests:` pass on 16 workers (`-n 16`) three runs in a row
- your final note gives the suite's time and the slowest ten tests, before and after
- all gates pass (see `docs/workflow.md`)
