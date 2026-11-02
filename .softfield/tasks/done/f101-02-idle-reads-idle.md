---
id: f101-02-idle-reads-idle
milestone: f101-uv-runner-run-command-stopped-when
difficulty: 3
depends_on: []
finding: f101-uv-runner-run-command-stopped-when-F2
files:
  - factory_dashboard/app.py
  - factory_dashboard/templates/_partials/running.html
tests:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
While the runner holds with nothing to run, the top bar and the Overview's Now show its idle line as it is ("Idle: 22 tickets wait for Claude's reserve · the week resets Mon 17:00"), not "Running: Idle: …" in green.

### Context
Read `def factory_status` in `factory_dashboard/app.py` and `factory_dashboard/templates/_partials/running.html`. In `tests/factory_dashboard/test_app.py`, `def _waiting` and `test_the_top_bar_says_what_the_factory_does_with_pause_or_resume` are the worked example for the top bar; in `tests/factory_dashboard/test_overview.py`, `test_a_live_run_between_jobs_shows_its_activity` is the one for Now.
- Since F101 the runner writes its run's activity as a full sentence starting with `Idle: ` while it holds, for example `Idle: nothing is ready` or `Idle: 2 tickets wait for Claude's reserve · the week resets Mon 16:00 · waiting for you: 1 sign-off`. It has no `waiting_until`.
- The dashboard doesn't import the runner's constants: `PICKING` in `factory_dashboard/app.py` repeats the runner's words with a comment. Do the same for `Idle: `.
- The top bar: an activity that starts with `Idle: ` is the status's words as they are, with no tone (as "Idle: nothing to do" has today) and the Pause button. A running job still wins: the check comes after the job's.
- Now: the same activity is shown as it is, without "Running: " before it. The template's `paused by you` branch is the example.
- Every other activity keeps "Running: " in both places.

### Done when
- a live run whose activity is `Idle: 2 tickets wait for Claude's reserve · the week resets Mon 16:00`: the top bar on the Overview, Planning, Tickets and the live partial says exactly that, with the Pause button, and its pill carries neither `good` nor `serious`
- the Overview's Now shows the same words, and "Running: Idle" appears nowhere on the page
- a live run whose activity is `check-all on main` still reads "Running: check-all on main" in both places
- "Idle: nothing to do" (picking, with an empty queue) is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 3718
gate_failures: ['stopped']
tokens: 3096396
```
