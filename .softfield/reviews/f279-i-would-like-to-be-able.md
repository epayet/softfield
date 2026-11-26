# Review: F279, The queue: the whole factory's line on one page, in the runner's order

**Status:** round 1 done, two fix tickets queued (f279-10, f279-11). Score 6/10. One blocking point (the page's order over pace) and the cut-off belt key were fixed by the review.

### 1. What changed
- A new page, The queue (`/queue`), shows every project's jobs and tickets in the order the runner will take them. One sentence at the top says what drives that order now, and each row opens to show its goal, why it sits there, what it waits for and any pre-flight problem.
- The runner works this list out at each pick and stores it. The Overview's Next in line and `softfield run --dry-run` now show that same list, and the map's queue station opens the page.
- While Claude is over pace, a lead ticket that only fills the gap now goes after every project's developer tickets, as ADR 50 says (before, it only had to wait for its own project's).
- Matches the mock-up, except that on the Overview a job row has no number yet (f279-10). The link reads "The whole queue ›" without the mock-up's counts, as D7 says.

### 2. How to test it yourself
1. On your phone, open the Overview, find the Queue panel and tap "The whole queue ›".
2. Check that the sentence at the top says the same as the top bar's allowance (today: "Over pace: developers first, the lead when nothing else can").
3. Under Can go, the developer tickets come first and the lead tickets marked "goes when nothing else can" come after them; travel-companion's tickets show their plate. Tap a row to open its details.
4. On the Planning page, approve a plan. The queue shows "On its way … applied at the next pick" until the runner's next pick, then lists the plan's tickets.
5. Run `softfield run --dry-run` in a terminal: the list is in the same order as the page.

### 3. Done when, as of now
- **Met:** f279-01 to f279-05 are merged.
- **Met:** "The whole queue ›" opens `/queue`, and its sentence and the Overview's both read "Over pace", as the allowance does. The Overview's first rows are `/queue`'s first rows, because both come from the stored plan.
- **Met:** travel-companion's tickets show among softfield's, with their plate. Tapping a row opens its goal, why it's there, what it waits for and its pre-flight problems.
- **Your check:** the "On its way" line after approving a plan (the tests cover it, but no request was waiting on the live database), and `softfield run --dry-run` showing the same order.

### 5. Decisions made along the way
- **Over pace, the Can go list puts every project's tickets that can start before any lead ticket that only fills the gap.** That is the order `project_round`'s two passes run them in. Before this fix, 89 of softfield's lead tickets were listed above its 6 developer tickets. *The review.*
- **The belt's key is a line of text under the picture, not inside it.** Inside the picture it was cut off at "orange: the lea" on every screen. *The review.*
- **The map's queue station still counts the floor's own queue; only its link goes to `/queue`.** D8 asks for a link, not a list. *Developer, f279-05.*
- **With no plan stored yet, the Overview shows its old Queue panel.** That keeps a new install readable until the runner's first pick, at the cost of a second way to order the queue. *Developer, f279-04, as its ticket asked.*

### 6. What next
- **Factory:**
  > Simpler: once every factory has a stored plan, drop the pre-plan branch of `factory_dashboard/templates/_partials/queue.html` and the queue, queued_jobs, lane and next context `factory_dashboard/overview.py` builds for it, so the dashboard never orders tickets itself (about 80 lines).

  > On The queue, show about when each row should start, from the developers' runway and where the lead fills the gap.

  > The planner's "where the work stands" reads the runner's stored plan, so its answers about when a card will be done match The queue.

### 8. How the work went
- f279-02 made the plan follow D5 across projects but kept each project's tickets in board order, so the page contradicted its own heading over pace. Its test had one ticket per project. The review's new test gives a project both a lead ticket and a developer ticket.
- The checkpoints caught that f279-04 shipped with no test, but missed the card text glued to the who ("the leadF279") in the same diff. f279-08's test then matched `the lead\s*F1`, which accepts the glued text.

### 9. What clogged the factory line
- f279-03, a new page built from a mock-up (difficulty 5), failed three times on the local model (about 65 min) before the lead built it in 35 min for $2.48. A new page with a mock-up should go to the lead at planning.
- f279-05 lost 63 min on a failed first attempt (all-tests) before a 22-min pass.

<!-- runner report -->
<!-- runner report -->
