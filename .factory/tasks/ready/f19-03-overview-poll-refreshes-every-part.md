---
id: f19-03-overview-poll-refreshes-every-part
milestone: f19-will-i-need-to-refresh-planning
difficulty: 3
depends_on: []
files:
  - factory_dashboard/templates/overview.html
tests:
  - tests/factory_dashboard/test_overview.py
finding: f19-02-F1
---

### Goal
A browser test shows the Overview's single `/live` poll really refreshes Needs you, Now, Queue, the allowance and the top bar's facts, and the markup is fixed if it doesn't.

### Context
Read `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py` (`test_the_live_partial_answers_on_its_own_for_htmx`); for a browser test follow `test_pause_survives_a_stale_live_poll` in `tests/factory_dashboard/test_app.py` (`page`, `route`, `REFRESH`).
- f19-02 only counts `hx-get="/live?project=coucou"` on the page (now 1); nothing checks that the content of Now, Queue or the allowance changes after a poll, so a poll that swaps nothing would pass.
- The poller carries `hx-swap-oob="#now,#queue,#allowance"` on the requesting element itself, which htmx doesn't read there; the sections in `factory_dashboard/templates/_partials/running.html`, `factory_dashboard/templates/_partials/queue.html` and `factory_dashboard/templates/_partials/allowance.html` carry `hx-swap-oob="innerHTML"` and rely on the response's own out-of-band pass. The ticket f19-02 asked for `hx-swap="none"` with `hx-select-oob`.
- The Overview no longer has `#live-poll`, so the top bar's status and `#live-facts` now refresh only when `window.liveIdle()` is true.

### Done when
- a browser test serves `/live` answers that differ between polls (a running job's name in Now, a queue row, an allowance figure, a Needs you item) and checks each new text appears on `/` within one `REFRESH`, from one `/live` request per poll
- the top bar's status words also change on `/` after a poll
- the stray `hx-swap-oob` on the poller is gone unless the test shows it is needed
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
