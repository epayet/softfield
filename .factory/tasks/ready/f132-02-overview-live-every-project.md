---
id: f132-02-overview-live-every-project
milestone: f132-the-overview-shows-the-whole-factory
agent: lead
difficulty: 6
depends_on: [f142-01-notify-every-project]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/app.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/templates/_partials/needs_you.html
  - factory_dashboard/templates/_partials/project_plate.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_app.py
---

### Goal
The Overview's live part (Now, the Queue, Next in line and Needs you) shows every project, the same whichever project is picked, each item with its project's plate.

### Context
Read `.factory/cards/f132-the-overview-shows-the-whole-factory.md` (D2–D6) and build the Proposed side of `.factory/cards/f132-mockup/overview.html`: its Needs you, Now and Queue panels, and the `.proj` plate.
- `factory_dashboard/overview.py`: `_live_context`, `running_jobs`, `live_runs`, `queue`, `queued_jobs`, `needs_you`, `notices`; Next in line comes from `live_line` in `factory_dashboard/line.py` (`["now"]["next"]`). f142-01 (built before this) already adds every project's stored items to `data-notices`: keep its ids and words.
- The runner's real order across projects is `project_round` in `runner/loop.py` (D5); `runner/metrics.py`'s `projects_in_order` gives the projects.
- Add `every_project` (D4) to `factory_dashboard/overview.py` and `many_projects` to `render` in `factory_dashboard/app.py` (D3); the plate is one partial, `factory_dashboard/templates/_partials/project_plate.html`, and `.proj` joins `factory_dashboard/static/dashboard.css` beside `.pill`, in the existing tokens only.
- Each item knows its project: `Running`, `Queued`, `QueuedJob` and `Need` gain a `project` field (or the context pairs each with its name); every link in these partials carries the item's own `?project=`.
- `/live` keeps one poll and the same ids (`#now`, `#queue`, `#needs-you`, `#live-facts`): the poll in `factory_dashboard/templates/base.html` and `factory_dashboard/static/notify.js` read them. The top bar's status is f132-01's, unchanged.
- With no job running anywhere, Now shows one line for the runner (the first live run's activity, as the top bar ranks it), not one per project.
- The page's other panels (the floor, While you were away, Savings) are later tickets: leave them as they are.

### Done when
- softfield running a planner job, travel-companion and coucou between jobs: the Overview for each of the three projects shows the same Now (the softfield job, with its plate) and no "picking the next ticket" line
- no job anywhere: Now shows one between-jobs line
- Needs you has one desk line per project with desk items, each with its plate, its count, its top three and "Open ›" to that project's `/planning`; a project with an empty desk has none; every project's notices show, each with its plate
- Next in line lists queued jobs of every project first, then the tickets that can run project by project in the order, then the waiting ones; a first project with nothing that can run gets one "Passed over" line with its first ticket's wait
- the Queue says "63 tickets waiting: softfield 54 · travel-companion 9" for 54 and 9 ready tickets, and only the total with one project
- with one project only, no plate shows anywhere and the panels read as today
- every row's link carries its own project
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
