---
id: f62-03-projects-planning-jobs-name-the-card
milestone: f62-claude-opus-review-on-overview-does
difficulty: 3
depends_on: [f62-01-now-names-the-card]
finding: f62-claude-opus-review-on-overview-does-F1
files:
  - factory_dashboard/projects.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/coming.py
  - factory_dashboard/jobs.py
  - factory_dashboard/templates/jobs.html
tests:
  - tests/factory_dashboard/test_projects.py
  - tests/factory_dashboard/test_coming.py
  - tests/factory_dashboard/test_jobs.py
---

### Goal
The Projects page's running line, the Planning room's "after …" wait and the Jobs list's Ticket column name the card a ticketless review, planner reply or checkpoint works on (its upper-case key, e.g. "review F158"), instead of the bare role or "–".

### Context
- `job_card` in `factory_dashboard/overview.py` names a ticketless job's card (key, title, line) from its role, its milestone key and the milestone's title (F62 D1). Every place below calls it; nothing else looks the card up.
- Projects: `running_now` in `factory_dashboard/projects.py` builds `NowJob` from `running_jobs`; `factory_dashboard/templates/projects.html` line 22 prints `job.role` when there is no ticket. Print "review F158" and the card's title there, the key linked to `/planning/f158?project=<project>`.
- Planning room: `_what` in `factory_dashboard/coming.py` returns `job.ticket or job.role`, so a message waits "after review". With a card it returns "review F158".
- Jobs list: `list_jobs` in `factory_dashboard/jobs.py` already joins `milestones m`; `factory_dashboard/templates/jobs.html` prints "–" in the Ticket column for a ticketless job. Print the card's key there, linked to `/planning/<lower-case key>?project=<project>`, for a review, planner or checkpoint job.
- A job with neither ticket nor card, or of another role, reads as today everywhere.
- Fixtures use a full card key like `f158-milestones-don-t-show-me-their`, as the live database has.

### Done when
- Projects page: a running review on `f158-…` reads "review F158" with the card's title, the key linked to its planning page
- Planning room: a message waiting behind that review reads "after review F158"
- Jobs list: that review's Ticket cell is `F158` linked to `/planning/f158`; a developer job keeps its ticket link; a ticketless job of another role keeps "–"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
