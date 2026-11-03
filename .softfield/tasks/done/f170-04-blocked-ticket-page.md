---
id: f170-04-blocked-ticket-page
milestone: f170-there-s-a-blocked-ticket-that
difficulty: 3
depends_on: [f170-03-desk-offers-the-fix]
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/planning.py
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
A blocked ticket's page says why it is blocked, links to its card and the card's thread, and has the desk's buttons: "Approve the lead's fix", "Try again as it is" and "Set aside".

### Context
Read `.softfield/cards/f170-there-s-a-blocked-ticket-that.md` (D4) and the mock-up to build, `.softfield/cards/f170-mockup/blocked-ticket-page.html` (Proposed). One thing differs from the mock-up: leave out "Nothing waits behind it.", because nothing counts the tickets waiting behind a blocked one.
- The panel follows the set-aside one already on the page: `#aside` in `factory_dashboard/templates/ticket.html` and `.aside` in `factory_dashboard/static/dashboard.css` (f159). Add a `blocked` panel beside it with the same plate (`Blocked`, `.softfield/tasks/blocked/`), reusing the `.aside` rules where they fit; a new rule uses the existing tokens only. Its test to follow: `test_a_later_ticket_page_shows_set_aside_panel` in `tests/factory_dashboard/test_tickets.py`.
- The facts come from what f170-03 added for the desk's blocked item in `_blocked` (`factory_dashboard/planning.py`): the runner's reason, the lead's first point and its `replan`'s title, or that the lead is still looking. Move that lookup into one public function in `planning.py` that takes the ticket and returns those facts (None when the ticket has no open `blocked` item), and use it from `_blocked` and from `ticket_page` in `factory_dashboard/tickets.py`, so the desk and the page say the same.
- The buttons post exactly what the desk's do (`approve_plan` with the card's key, `queue`, `set_aside`, with the ticket's id) and show the panel on its way at once, as the set-aside panel's Queue it does (`.sent`, a dashed `--hazard` line saying "at the runner's next pick").
- Links: "Read the fix on F21's thread ›" to `/planning/<card>`, "F21's card ›" to `/milestones/<the card's full key>`. The crumbs' first link becomes the card's name ("F21, The lead's briefs", from the card's heading, as the board names it) to `/milestones/<full key>`, on every ticket page, not only blocked ones.
- A bug ticket (no card): the panel says why it is blocked, with "Try again" and "Set aside" only, and no links to a card.

### Done when
- f21-03-trim-owner with an open `blocked` item "f21-03-trim-owner blocked: the lead ticket changed nothing" and, on F21's thread, the runner's look then a lead reply whose first point is "What went wrong: owner.md has grown past the ticket's target" and whose `replan` is "Set aside f21-03, trim owner.md": its page shows a Blocked panel with "The lead ticket changed nothing.", that point, that title, an "Approve the lead's fix" button posting `approve_plan` with subject `f21`, and links to `/planning/f21` and `/milestones/f21-lead-briefs`
- the same with no lead reply yet: the panel says the lead is reading the work and its logs, with "Try again as it is" and "Set aside" only
- once the item is resolved, the page has no Blocked panel
- a blocked bug ticket's page: "Try again" and "Set aside", no card links
- every ticket page's first crumb names its card and links to `/milestones/<full key>`
- the desk's blocked item says what it said before this ticket (its tests unchanged and passing)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 7276608
logs: .softfield/var/runs/20261103-110556/f170-04-blocked-ticket-page
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
