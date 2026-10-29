---
id: f184-01-runner-dot
milestone: f184-when-check-all-is-running-the
difficulty: 2
depends_on: []
files:
  - factory_dashboard/app.py
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/_partials/bar_status.html
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
While the runner works on its own between jobs (check-all, the gates, the warm-up, picking the next ticket), the top bar's dot is green and breathes instead of the grey of "nothing happening".

### Context
Read `.factory/cards/f184-when-check-all-is-running-the.md` (Outcome, "Why it is grey today", D1), then `Status` and `factory_status` in `factory_dashboard/app.py`, and the `.factory-status .dot` rules in `factory_dashboard/static/dashboard.css`.
- The picture to build is `.factory/cards/f184-mockup/runner-dot.html` (Proposed).
- The new dot value is `runner`. Set it on the `Running: {activity}` return at the end of `factory_status`, and on the "Pausing after …" return when no job is live; there, name the activity instead of "this job" when the run has one that isn't the picking or idle line (`Pausing after check-all · f172-07-fast-lane-in-the-card`). Leave every other return as it is: "Idle: …" and the paused hold stay `idle`.
- The ⏸ sign's `data-asked` in `factory_dashboard/templates/_partials/bar_status.html` builds the words shown at the tap by reversing the parts after "Running: " (made for "Running: coucou · f1-04-live"); for one project's "Running: check-all · f1-04-live" it would read "Pausing after f1-04-live · check-all". Make it match what the server then says, without changing the multi-project words.
- `factory_wide_status` ranks by words and by `dot in ("lead", "developer")`: leave it ranking a runner-busy project as it does today (with the other `Running: ` words).
- CSS: `.factory-status .dot.runner` uses `var(--good)` with the same 18 % halo as `.dot.lead` and `.dot.developer`, and joins their `breathe` animation under `prefers-reduced-motion: no-preference`. Update the comment above `.factory-status` to say what green means.
- Tests: `test_the_top_bar_says_what_the_factory_does_with_pause_or_resume` in `tests/factory_dashboard/test_app.py` is parametrised by setup, words and dot; add cases there, with a live run whose `runs.activity` is `check-all · f1-04-live` and no live job, following the existing setups.
- The dashboard is English only: no translation needed.

### Done when
- a live run with activity `check-all · f1-04-live` and no live job shows "Running: check-all · f1-04-live" with the `runner` dot on `/`, `/planning`, `/tickets` and `/live`
- the same with a pause asked reads "Pausing after check-all · f1-04-live" with the `runner` dot, and the ⏸ sign's `data-asked` holds the same words
- "Idle: nothing to do", "Idle: …" lines and "Paused by you since …" keep the `idle` dot; running jobs keep `lead` or `developer`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
