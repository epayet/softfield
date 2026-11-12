# Review: F220, switching project from an inner page goes back to that tab's own page

## Sign-off sheet

### 1. What changed
Picking another project in the top bar's picker while you are inside something (a planning thread, a card, a ticket, a job, a run, a project's page) now takes you to that tab's own page for the new project: Planning, Board, Tickets, Jobs, Runs or Projects. Before, it kept the same address, which in the other project was a "Not found", a different card under the same number, or nothing visible at all. From a page every project has (Board, Planning, Tickets, the Overview, the Milestones list…) it stays on that page, as before.

The card had no mock-up and no after pictures: nothing on the page looks different, only where the picker lands.

### 2. How to test it yourself
1. On your phone or laptop, open the dashboard on softfield, open a card from the Board, and pick coucou in the picker: you land on coucou's Board.
2. Open a discussion from Planning and pick another project: you land on that project's Planning.
3. Open a ticket from Tickets and pick another project: you land on its Tickets list.
4. Open a project's page from Projects and pick another project: you land on Projects with that project picked.
5. Open the Milestones list (from the Board) and pick another project: you stay on the Milestones list.

### 3. Left for later
Nothing set aside. One small gap in the tests is noted below (a ticket's page isn't in the picker test) and judged not worth a run.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-06, run 20261106-011143 ([session](../sessions/2026-11-06-0111.md)): f220-01 merged by the local model in 1 attempt (model 21 min, gates 14 min, 3.6M local tokens in); no lead tokens on building it.
- Lessons: a one-attribute change with the decisions spelled out in the card (D1–D3) and the test shape given in the ticket is exactly what the local model does well, first time. The ticket's hint to find the form by its select rather than its place in the bar (D3) made the test survive f132-08's move.

### 6. What next
- **Product:** product work is on hold; nothing proposed.
- **Factory:** the session report flags "edited existing tests" for any ticket that touched a test file, even when it only appended new tests (as here). Telling appended from changed tests would spare reviews a false lead; worth a small runner ticket when the reports are next touched.

### 7. What clogged the factory line
For this milestone, nothing beyond its own 35 minutes: one attempt, no failed gates, no parks, no waits on other tickets. The 14 minutes of gates are the full suite running for a one-line template change; that is the factory-wide cost of the gates, not this card's.

<!-- runner report -->
<!-- /runner report -->

## What was built
- `factory_dashboard/templates/base.html`: the picker's form gets `action="{{ picker_to or active }}"`, so it submits to the lit tab (D1). A page without `active` gets an empty action, which reloads the current address as before.
- `factory_dashboard/milestones.py`: the Milestones list passes `picker_to: "/milestones"` (D2).
- `tests/factory_dashboard/test_app.py`: one parametrised test over 13 pages, finding the form by its project select (D3). It fails without the change (no `action` at all). The commit only appended to the test file; no existing test was changed.

I checked every page's `active`: threads and proposals `/planning`, a card `/board`, a ticket `/tickets`, a job `/jobs`, a run `/runs`, a project `/projects`; Timeline, Agents, Bench and the Line have their own address, which every project has. The new test passes.

## Findings
- **F1 (nit, report):** the picker test leaves out a ticket's page (`/tickets/<id>`), which Done when names, and a proposal's page. Both set `active` and work through the same template expression, so the gap is only in coverage. Not worth a run.

No checkpoint findings to judge. Score: 9/10.

## Workflow observations
- No French involved (factory dashboard only).
- Clean first-attempt merge from a small, well-specified ticket; the card's plan read the code and listed exactly what each inner page did wrong, which made the review quick.
