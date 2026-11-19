---
id: f272-01-job-clock-in-the-bar
milestone: f272-i-want-to-know-from-the
difficulty: 3
depends_on: [f256-01-top-row-in-line]
files:
  - factory_dashboard/app.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/bar_status.html
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The top bar says how long the job at work has been running and, on a ticket's job, which attempt it is: a "Job" plate after the words on a wide screen, a line in the words' hover title under 1200 px, and a line in the tapped words on a phone.

### Context
Read `.softfield/cards/f272-i-want-to-know-from-the.md` (D1 to D5) and build the Proposed of `.softfield/cards/f272-mockup/job-clock.html`: its CSS for `.job` and `.jobline` is the picture to copy, on the tokens of `factory_dashboard/static/dashboard.css`.
- `factory_dashboard/app.py`: `Status`, `factory_status` and `factory_wide_status`. The job is the `job` that `factory_status` already finds; in the paused branch, the live planner job.
- `factory_dashboard/overview.py`: `Running` and `running_jobs` (it has `attempt`, `role` and `elapsed`; add the start time if you need it). `attempt_words(job, max_attempts)` goes here.
- The project's `max_attempts`: `_config` in `factory_dashboard/line.py` reads a project's config from its repo; reuse it (call it inside the function, as `factory_status` imports `line` today, to avoid an import cycle). Only read it when a developer or last-attempt job is live.
- The time's words: `factory_dashboard/machine.py`'s `on_for`, as the "On" plate uses it.
- `factory_dashboard/templates/_partials/bar_status.html`: the `.uptime` plate and the `.on` line (F251) are the examples for `.job` and `.jobline`. The words' `title` is new; the dot's `title` and `aria-label` stay one sentence each as today, the title with the job line added.
- `factory_dashboard/templates/_partials/running.html`: the "attempt" pill takes `attempt_words`, and is left out when it is None.
- `tests/factory_dashboard/test_app.py`: `test_the_top_bar_says_what_the_factory_does_with_pause_or_resume` and its setups (`_running`, `_lead_ticket`, `_pause_held_planner`, `_waiting`) show how the bar is tested with a running job; `test_phone_top_bar_is_compact_and_tabs_scroll` shows the Playwright measuring at a width.

### Done when
- with a developer's job on attempt 2 started 14 minutes ago and `max_attempts = 3`, the bar's `.job` plate reads "14 min" and "attempt 2 of 3", and the words' title ends "Job running 14 min · attempt 2 of 3"
- a `last-attempt` job reads "attempt 3 of 3, the last"; a lead ticket's "attempt 2"; a planner's (also while paused, "the lead is answering you") the time alone, with no "attempt" anywhere in the bar
- between jobs, waiting for Claude, idle and stopped, the bar has no `.job` plate and no job line
- with two projects, the plate is the job's whose words the bar shows
- at 1280 px the plate is visible and the top row stays one line; at 1000 px it is hidden; at 390 px, after a tap on the dot, the words show the job line above "Computer on …"
- the Overview's "Now" panel shows "attempt 2 of 3" on that developer job and no attempt pill on a planner's
- `/live` carries the plate and the line, so a page's poll updates the time without a reload
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
