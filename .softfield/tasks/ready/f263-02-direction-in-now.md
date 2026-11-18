---
id: f263-02-direction-in-now
milestone: f263-on-the-console-run-you-can
difficulty: 4
depends_on: [f263-01-direction-kept-in-the-database]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
While a developer's last attempt runs, the Overview's Now panel shows the lead's direction it works from: its first line on a plate under the ticket's title, the whole text when tapped.

### Context
- The picture to build: the Proposed "Phone · Now" frame of `.softfield/cards/f263-mockup/direction-on-overview.html`. Decisions D2 and D3 in `.softfield/cards/f263-on-the-console-run-you-can.md`.
- The text is in `jobs.direction`, on the `direction` job's row (f263-01). For a running job whose role is `last-attempt`, take the newest `direction` job of the same `ticket_id` that started before it and has a `direction`.
- Add to `Running` in `factory_dashboard/overview.py` the direction's text, its job id, its cost and its start, filled in `running_jobs`; None for every other job.
- Draw it in `factory_dashboard/templates/_partials/running.html` between the title and the readouts, as a `details.direction`: the summary holds "The lead's direction", "Opus · HH:MM" (the local start) and the first line (`first_line` in `runner/console.py`); opened, the whole text through `_to_html` in `factory_dashboard/milestones.py`, and a link to `/jobs/<id>` with its cost. Add the `.direction` rules to `factory_dashboard/static/dashboard.css` from the mock-up's "proposed" block; no new colour token.
- The panel is redrawn every 5 s: make `window.liveIdle` in `factory_dashboard/templates/base.html` return false while a `details.direction` is open, beside its existing `details[open]` check.

### Done when
- a running `last-attempt` with a direction before it shows the plate with its first line; the summary's first line is clamped to two lines
- opening the plate shows the whole text, escaped, and the link to the direction's job; while it is open the Overview doesn't redraw Now, and folding it lets it redraw
- a first attempt, a lead job, or a last attempt whose direction has no stored text shows no plate, as today
- with two directions on the ticket, the newest one before the attempt shows
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
