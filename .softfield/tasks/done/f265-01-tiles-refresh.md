---
id: f265-01-tiles-refresh
milestone: f265-the-factory-now-section-in-planning
difficulty: 2
files:
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On `/planning`, The factory now and The lead's window refresh every 5 s with the desk, from the desk's own poll, so what's running and the gauges stay current without a reload.

### Context
Read D1–D3 in `.softfield/cards/f265-the-factory-now-section-in-planning.md`.
- `factory_dashboard/templates/planning.html`: `#tiles` holds `#factory-now` and `#lead-window`, outside every poll. `#live-desk` polls `/planning{{ q }}` every 5 s and keeps only `#desk` (`hx-select`).
- The example to follow: `#live-needs-you` in `factory_dashboard/templates/overview.html`, which takes its other parts out of the same answer with `hx-select-oob="#now:innerHTML,…"`.
- Add `hx-select-oob="#factory-now:innerHTML,#lead-window:innerHTML"` to `#live-desk`, and make its `hx-disinherit` name both `hx-select` and `hx-select-oob`, so the buttons inside the desk (Dismiss, Approve the lead's fix, Try again, Set aside) still draw their answer in their own status `span`.
- Leave `#live-desk-coming`, `#tiles` and the page's script as they are. No change to `factory_dashboard/planning.py`: the full page already renders both tiles.
- Browser tests open the page with `_open(page, serve())`; follow `test_the_desk_poll_moves_an_answered_seed_to_the_answers` and its `LIVE` wait in `tests/factory_dashboard/test_planning.py`. A running job is written the way the existing `#factory-now` tests in that file write one (search for `factory-now` or `Running`).

### Done when
- `/planning`'s HTML: the element with `id="live-desk"` carries `hx-select-oob="#factory-now:innerHTML,#lead-window:innerHTML"` and an `hx-disinherit` naming both `hx-select` and `hx-select-oob`; no other element on the page carries `hx-select-oob`
- in the browser: the page opens with nothing running ("Nothing running right now." in `#factory-now`); a job is then written to the database; within a poll `#factory-now` reads "Running" and names it, without a reload
- in the browser: Dismiss on a refused note still shows "Asked" (`test_dismiss_takes_the_item_off_at_once_and_a_reload_keeps_it_off` passes unchanged)
- the listed `tests:` pass, and the new ones fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1765
gate_failures: []
tokens: 2213200
```
