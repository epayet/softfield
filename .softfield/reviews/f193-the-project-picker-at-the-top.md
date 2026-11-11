# Review: F193, the project picker follows the owner's project order

## Sign-off sheet

### 1. What changed
The project picker in the top bar now lists the projects in the same order as the Projects page, instead of by name. Today that is travel-companion, softfield, coucou (it used to show coucou, softfield, travel-companion). A forgotten project is still left out. A page opened on a project that isn't listed still shows it, last and selected.

No mock-up for this card: the control looks the same, only the order of the names changes.

### 2. How to test it yourself
1. On your phone, open the dashboard and tap the project picker at the top: the names come in the Projects page's order.
2. On the Projects page, drag a project to another place and send the new order.
3. After the runner's next pick, reload any page and open the picker again: it has the new order.

### 3. Left for later
Nothing. No bug tickets were set aside.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-02: the lead planned the card (Opus, about $0.53).
- 2026-11-06 ([session](../sessions/2026-11-06-0111.md)): f193-01 merged by the local model on its second attempt. The first ran 80 minutes to its timeout; the second passed in 37. All local, no Claude tokens.
- 2026-11-11: the lead reviewed it (round 1) and made the test cover the whole ticket.

Lessons:
- A three-line change still cost the local model almost two hours. That is the same slowness F195 is looking into, not something new here.
- The developer's test checked only the main point of the ticket. The review added the rest, and the checkpoint should have caught it.

### 6. What next
- **Product:** product work is on hold until you ask.
- **Factory:** the picker and the Projects page now read the same list. When ticket "Done when" items each name something to check, the checkpoint should match each one to an assertion in the test. Three of four were missing here, and that is a pattern worth its prompt.

### 7. What clogged the factory line
- **80 minutes on a timed-out first attempt** (job 1888, 3.0M tokens in) for a difficulty-1 ticket. To unclog: F195, the work on the local model's speed.
- **About 3½ days between planning (2 Nov) and the build (6 Nov):** the card waited its turn on the board, behind other work while Claude was limited. Nothing to change for this card alone.

---

## What was built
`render` in `factory_dashboard/app.py` used to run its own query, sorted by name. It now takes the names from `metrics.projects_in_order`, the same list the Projects page and the runner use. That list already leaves forgotten projects out and breaks a tie by name. The old way of adding a page's unlisted project at the end is kept. (commit `8fb1e529b`)

## Findings and resolutions
- **F1 (should-fix, fixed by the lead):** the new test checked the order only. Three of the ticket's Done when points went unchecked: a forgotten project left out, an unlisted page project shown last and selected, and a reorder showing on the next page. The commit also removed the SQL's own forgotten filter, so nothing in the dashboard tests guarded it any more. The test now adds a forgotten project at the top of the order, opens a page on it, and reorders between two requests. `tests/factory_dashboard/test_app.py`.
- **F2 (nit, report only):** the local model took 117 minutes and 4.1M tokens for a three-line change. That belongs to F195.

The checkpoints found nothing on this ticket. F1 was visible in the diff they read, so it is counted as missed.

No French: the change has no wording.

## Workflow observations
The plan named the function, the example just above it and the test to extend, and the change itself came out right. The test was the weak part: the developer asserted the headline and stopped. The checkpoint stand-in (copilot-auto) didn't cross-check the test against Done when either.

<!-- runner report -->
<!-- /runner report -->
