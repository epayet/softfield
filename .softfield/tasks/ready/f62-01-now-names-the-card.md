---
id: f62-01-now-names-the-card
milestone: f62-claude-opus-review-on-overview-does
difficulty: 3
depends_on: [f132-02-overview-live-every-project, f132-06-jobs-runs-every-project]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/app.py
  - factory_dashboard/projects.py
  - factory_dashboard/planning.py
  - factory_dashboard/jobs.py
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/templates/projects.html
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/jobs.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_projects.py
  - tests/factory_dashboard/test_jobs.py
---

### Goal
A job with no ticket (a review, a planner reply, a checkpoint) names its card wherever a running or queued job is shown: the card's key linked to its page, its title, and one line on what the job does.

### Context
Read `.softfield/cards/f62-claude-opus-review-on-overview-does.md` ("What happens today" lists every place, and D1–D3). The picture to build is `.softfield/cards/f62-mockup/now-names-the-card.html` (Proposed, with the plate).
- `running_jobs` in `factory_dashboard/overview.py` already reads each job's card as `milestone`; add `job_card` and the role lines (D1, D2) beside it.
- `short_key` is in `runner/tasks.py`; the card title from its doc follows how `factory_dashboard/planning.py` gets `card_title` (`milestone_doc`).
- The ticket link in `factory_dashboard/templates/_partials/running.html` is the example for the card's link; the plate is the project plate partial and `.proj` that f132-02 added (`factory_dashboard/templates/_partials/`, `dashboard.css`).
- A due review's queue row is built in `factory_dashboard/line.py` (`"kind": "batch"`, with its `milestone`) and drawn in `factory_dashboard/templates/_partials/queue.html`; change the drawing and the words, not the floor's crate.
- The top bar words come from `factory_status` in `factory_dashboard/app.py` (both the status and the pause button's "Pausing after …" words use `job.ticket or …`).

### Done when
- a running review job on `f158-…`: Now shows `F158` linked to `/planning/f158`, the card's title, and "The lead reads what F158 built, before it's yours to sign off"; the top bar reads "Running: <project> · review F158"
- a running planner job shows "The lead answers you on F62's thread"; a checkpoint "Claude re-checks F51's merged tickets"
- a due review in Next in line shows its key, its card's title and "the lead reads what it built"; the words "a batch" are gone
- the Projects page's running line, the Planning room's running line and the Jobs list's Ticket column name the card the same way for a job with no ticket
- a job with a ticket shows as today; a job with neither ticket nor card (a probe) shows as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
