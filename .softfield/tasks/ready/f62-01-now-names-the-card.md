---
id: f62-01-now-names-the-card
milestone: f62-claude-opus-review-on-overview-does
difficulty: 3
depends_on: [f132-02-overview-live-every-project, f132-06-jobs-runs-every-project]
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On the Overview's Now panel, a running job with no ticket (a review, a planner reply, a checkpoint) names its card: the card's key linked to its page, its title, and one line on what the job does. The other places (top bar, Next in line, Projects, Planning, Jobs) are left for a later ticket.

### Context
The card is `.softfield/cards/f62-claude-opus-review-on-overview-does.md` (D1–D3); you need nothing else from it. The picture is `.softfield/cards/f62-mockup/now-names-the-card.html` (Proposed, with the plate).
- `running_jobs` in `factory_dashboard/overview.py` already joins the job's card as `m` (`milestones`) and reads `m.key AS milestone`; `milestones` also has a `title` column, so the card's title comes from the same query.
- Add `job_card` (D1) beside `running_jobs`, returning the short key upper-case (`short_key` is already imported in `overview.py` from `runner/tasks.py`) and the title, and one dict of role lines (D2) keyed by the job's `role`: `review`, `planner`, `checkpoint`. Any other role, a job with a ticket, or a job with no card gets no card line.
- In `factory_dashboard/templates/_partials/running.html`, line 11 draws the ticket's link; the card's link goes beside it in the same `{% if %}` chain, as an `<a class="proj" href="/planning/<lower-case key>">` with the key (D3), and the card title in the existing `running-title` line below. The project plate partial is not reused: it only draws when there are several projects.
- The test to copy is `test_a_running_job_with_no_tokens_says_no_tokens_reported_yet` in `tests/factory_dashboard/test_overview.py`: it builds a running job with `runner.metrics` and reads the `now` section. For a ticketless job pass `ticket_id=None`, a `role`, and `upsert_milestone(..., title=...)`.

### Done when
- a running review job on `f158-…` (title "Milestones on the board"): Now shows `F158` linked to `/planning/f158`, the title, and "The lead reads what F158 built, before it's yours to sign off"
- a running planner job on `f62-…` shows "The lead answers you on F62's thread"; a checkpoint on `f51-…` "Claude re-checks F51's merged tickets"
- a running developer job with a ticket shows its ticket link and title as today, and no `/planning/` link; a running job with neither ticket nor card shows no `/planning/` link and no card line
- each of these is its own test in `tests/factory_dashboard/test_overview.py`, and each fails without the change
- all gates pass (see `docs/workflow.md`)
