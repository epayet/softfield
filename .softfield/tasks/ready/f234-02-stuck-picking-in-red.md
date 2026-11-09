---
id: f234-02-stuck-picking-in-red
milestone: f234-if-it-says-running-picking-the
difficulty: 2
depends_on: [f234-01-turn-says-why-it-waits]
files:
  - factory_dashboard/app.py
  - factory_dashboard/overview.py
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/_partials/bar_status.html
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
When a run has said "picking the next ticket" for more than 5 minutes, the top bar says "No progress since HH:MM · picking the next ticket" in red with a steady red dot, not the green one.

### Context
Read `.softfield/cards/f234-if-it-says-running-picking-the.md` (D3, D4). The picture to build is `.softfield/cards/f234-mockup/stuck-picking.html` (Proposed).
- `runs.activity_since` (UTC ISO time) exists since f234-01. `LiveRun` and `live_runs` in `factory_dashboard/overview.py` gain it.
- In `factory_status` (`factory_dashboard/app.py`), before the final `Running: {activity}` return: a live run whose activity is `PICKING` and whose `activity_since` is older than 5 minutes at `now` returns `Status(f"No progress since {_clock(since)} · picking the next ticket", "fail", "pause", dot="stuck")`. No `activity_since` (an older run) keeps today's words.
- `factory_wide_status` ranks it with "Idle: …" (rank 4), below any "Running: …"; with several projects its project's name joins the words as for Idle.
- CSS: `.factory-status .dot.stuck` is `var(--fail)`, no halo, no `breathe`. The words take the existing `.factory-status .words.fail` rule: in `factory_dashboard/templates/_partials/bar_status.html`, the `.words` span gets the `fail` class when `bar_status.tone` contains `fail`. Add "red: no progress for 5 minutes" to the comment above `.factory-status`. Follow `.dot.runner` (F184). No hazard yellow here: the owner found it too close to the lead's orange.
- Tests: add cases to `test_the_top_bar_says_what_the_factory_does_with_pause_or_resume` in `tests/factory_dashboard/test_app.py`, following its setups.

### Done when
- a live run on "picking the next ticket" since 6 minutes ago shows "No progress since HH:MM · picking the next ticket" with the `stuck` dot and the words' `fail` class on `/` and `/live`
- the same since 1 minute ago still shows "Running: picking the next ticket" with the `runner` dot
- with two projects, a live job in one and a stale pick in the other, the bar shows the job; a fresh "Running: …" in one and a stale pick in the other shows the fresh one
- check-all or the gates since an hour keep "Running: …" and the green dot
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
