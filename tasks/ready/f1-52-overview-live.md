---
id: f1-52-overview-live
milestone: f1
depends_on: [f1-51-runner-activity]
difficulty: 5
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/templates/_partials/live.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Needs-you appears only when something needs the owner, and it refreshes with Running now, which also says what the runner is doing between jobs, when it waits for Claude, and when it runs on Claude's reserve.

### Context
Read `docs/milestones/f1.md` D3 and D8 (each "Amended 2026-10-02"). Follow the worked example: `factory_dashboard/overview.py` (`needs_you`, `running_jobs`, `runner_live`, the `/running` route), `factory_dashboard/templates/overview.html`, `factory_dashboard/templates/_partials/running.html` and `tests/factory_dashboard/test_overview.py`. `write_live` in `tests/factory_dashboard/conftest.py` writes a live run: add your rows in a function of your own there.
- f1-51 added three columns to `runs` (`runner/metrics.py`): `activity` (text such as "gates · f1-21" or "waiting for Claude"), `waiting_until` (ISO time, set while a pause for a limit lasts) and `reserve` (1 once the owner said yes to Claude's reserve for this command).
- **One partial, `/live`, every 5 s** (htmx, as `/running` is now): Needs-you, then Running now. `/running` goes; the page includes the partial.
- **Needs-you:** no section at all when it has no items (not "Nothing needs you").
- **Running now:**
  - with a live run and no running job: the run's `activity`, e.g. "Running: check-all on main"
  - with `waiting_until` set: "Waiting for Claude's limit to reset, until 01:40" in place of the job's "Live" line
  - with `reserve` = 1: an "on Claude's reserve" pill beside the job
  - a Claude job with tokens shows them like a local one: drop "elapsed time only, until it finishes"

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the rendered text, not only the status.

### Done when
- with no owner items, a live runner and an empty queue, the page has no Needs-you heading
- `/live` returns Needs-you and Running now together; a queue item disappears from it once a live run exists, without reloading the page
- a live run between jobs shows its activity; one waiting shows "until HH:MM"; one with `reserve` shows the pill
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
