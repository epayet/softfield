---
id: f3-05-line-panels
milestone: f3
depends_on: [f3-01-factory-line]
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On the Overview, one Now panel (what works, then the next three in line) replaces the Running now and Queue panels.

### Context
Read the `aria-label="Now"` section of `docs/milestones/f3-line-mockup/Line.dc.html` (markup to read, not a page to open), `_live_context` in `factory_dashboard/overview.py`, `live_line` in `factory_dashboard/line.py`, `factory_dashboard/templates/_partials/live.html`, `factory_dashboard/templates/_partials/running.html` and `tests/factory_dashboard/test_overview.py`.
- **Only this.** The floor stays on `/line` and `factory_dashboard/line.py` doesn't change: moving the floor to `/` is f3-14, and the clog panel is f3-15.
- **What works:** `running` and `runs` in `_live_context` already hold everything the mock-up's first block shows (attempt, elapsed, ticket, agent, role, title, tokens and turns, and the "Waiting for Claude's limit to reset, until HH:MM" line). Keep that data and its wording; the card becomes the top of `<section id="now">` headed "Now".
- **Next in line:** `live_line(conn, project, now.astimezone())["now"]["next"]` is the first three of the run order, each with `number`, `ticket`, `title` and `kind` (`lead` or `developer`). Add it to `_live_context`, so `/` and the 5 s refresh from `/live` both get it. Each row: number, ticket id, goal, then "the lead" or "a developer".
- **The drain command:** under Next in line, keep the old Queue panel's "N tickets waiting. Drain it with `<drain>`" line.
- **Removing:** the `#running` and `#queue` sections go. `queue` in `factory_dashboard/overview.py` stays: Needs you counts it.
- **Tests on the old panels:** move `section(html, "running")` assertions to `section(html, "now")`. The `queue_client` tests (a running ticket isn't queued, waits for an id, waits for an escalation, waits for Claude, ready now first) test `queue`'s `waits_for`, which the page no longer shows: make them call `queue(conn, PROJECT, NOW)` on the fixture database (opened from `db_path`, as the escalation test already does) and keep the same expected values. Don't weaken an assertion to "somewhere in the page".

### Done when
- with the `client` fixture, `#now` holds f1-04-live's attempt, agent, elapsed, title and "read … tokens · … turns", then "Next in line" with its numbered rows in run order, each with its ticket's goal ("Queued first." for f1-05-first); with more than three tickets in the run order, only three rows
- a run waiting for Claude's limit shows its wait and its clock in `#now`
- the page and `/live` have no `#running` or `#queue` section; the panels on `/` are needs-you, now, verdict, allowance, savings, spend
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 141600
logs: var/runs/20261003-132503/f3-05-line-panels
```
