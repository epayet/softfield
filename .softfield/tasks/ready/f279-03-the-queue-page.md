---
id: f279-03-the-queue-page
milestone: f279-i-would-like-to-be-able
difficulty: 5
depends_on: [f279-01-the-runners-plan]
files:
  - factory_dashboard/queue.py
  - factory_dashboard/templates/queue.html
  - factory_dashboard/app.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_queue.py
---

### Goal
A new page, The queue (`/queue`), shows the whole factory's line from the runner's stored plan: the sentence on what drives the order, then every job and ticket of every project in the runner's order, each row folding open for its details.

### Context
Read `.softfield/cards/f279-i-would-like-to-be-able.md` (D2, D6) and build the Proposed side of `.softfield/cards/f279-mockup/queue.html`, phone and wide screen.
- The data: `latest_queue_plan` in `runner/metrics.py` (f279-01) returns the plan as a dict, D2's fields; with no plan stored yet, the page says "The runner hasn't worked out a plan yet: it does at its next pick."
- Follow `factory_dashboard/bench.py` and `factory_dashboard/templates/bench.html` for a page of its own: a router included in `factory_dashboard/app.py`, a template extending `factory_dashboard/templates/base.html`.
- Factory-wide (F132 D2): `?project=` doesn't change what it shows; each row's links carry the row's own project (`/tickets/<id>?project=<name>`, `/planning/<card>?project=<name>`).
- Groups in order: fast lane, jobs, can go, waits; the waiting rows are grouped by the first ticket they wait for, each group a fold with its count, closed by default.
- The owner's requests not yet applied (`owner_requests` with `done` NULL and `dismissed` NULL, kinds approve_plan, reorder, project_order, queue, set_aside, pause, resume, reserve) show above the list with a dashed orange edge, "applied at the next pick".
- Styles join `factory_dashboard/static/dashboard.css` in the existing tokens only; the belt of the next crates is plain SVG in the template. Ornament never uses a status colour.
- The page refreshes every 30 s with htmx, held by `window.liveIdle()` as the other live parts are (`factory_dashboard/templates/base.html`); an open fold stays open.

### Done when
- `/queue` shows the stored plan's sentence, its facts, "worked out at HH:MM" and the rows in its order, numbered, each with its project's plate when there is more than one project, who does it, its card and why it is there
- tapping a ticket row opens its goal, waits, reason and pre-flight problems, with links to its ticket page and its card's thread, each with the row's project
- the waiting tickets show as folds, one per ticket they wait for, with counts
- a pending approve_plan request shows as on its way; once done, it is gone
- with no plan stored, the page says so and nothing breaks
- the page reads the same whichever project is picked
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
