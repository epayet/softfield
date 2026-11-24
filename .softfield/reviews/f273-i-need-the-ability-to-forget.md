# Review: F273, Forget a project from the Projects page

**Status:** round 1 done, ready for your sign-off. Score 8/10. One should-fix point (a test gap), fixed by the review.

### 1. What changed
- Each project in the Projects page's Archived bay has a Forget button beside Unarchive, quieter. Pressing it opens a striped question under the project (no pop-up): what leaves, that nothing is deleted, where its folder is, how to bring it back, and how many items for you go with it.
- "Yes, forget it" turns Forget into a dashed orange "Forgetting…" at once, with "On its way…". At its next pick the runner forgets it as `softfield forget` does. It refuses a project that isn't archived, or whose app is still up.
- If an archived project's app is still up, the project shows its app row (Stop, Logs) and Forget is greyed out with "Its app is running: stop it first, then Forget."
- No project is archived on the live database, so neither the page nor the after pictures can show the bay; the tests cover it. Otherwise it matches the mock-up, except the Forget icon is a struck square, not a ring, because the theme keeps every part square.

### 2. How to test it yourself
1. On the Projects page, press Archive on coaster-ranker, and wait for the runner's next pick.
2. Open the Archived bay and press Forget. Read the question, press "Keep it", and check that nothing changes.
3. Press Forget again, then "Yes, forget it". It turns dashed orange "Forgetting…" at once.
4. After the runner's next pick, coaster-ranker is gone from the bay, Needs you and the project picker.
5. Run `softfield init` in `~/projects/epayet/coaster-ranker` and choose Continue: it comes back.

### 3. Done when, as of now
- **Met:** f273-01 and f273-02 are merged.
- **Your check:** archive coaster-ranker, Forget it from the bay, see "Forgetting…" at once and the project gone after the next pick, then bring it back with `softfield init`'s Continue. The tests cover each step, but the live database has no archived project yet.

### 5. Decisions made along the way
- **The runner refuses a forget while the app is starting or failed an update, not only while it runs.** This matches the page's own "up" (where it offers Stop), so the button and the guard agree. *The lead, f273-01.*
- **The Forget icon is a struck square, not the mock-up's struck ring.** The theme's square-parts rule (f81-02) allows no rounded corners. *The lead, finishing f273-02.*
- **The "On its way" line in the Archived bay uses the plates' style (mono, hazard yellow), not the mock-up's orange.** One look for every waiting line on the page, Unarchive's included. *The lead, finishing f273-02.*

### 6. What next
- **Product:** on hold, as you asked; nothing proposed.
- **Factory:**
  > Bring a forgotten project back from the Projects page, so I don't need a terminal for softfield init's Continue.

  > Projects-page button tickets with browser tests (f124-02, f262-02, f273-02) all escalated after hours on the local model on 24 Nov: send tickets that add an htmx button with Playwright tests to the lead, or split the browser tests into their own ticket.

  > runner/requests.py's _forget_project lists the app's "up" states itself while factory_dashboard/stacks_routes.py has UP for the same set: move UP into runner/stacks.py and use it from both, so Forget's button and the runner's guard can't drift apart.

### 8. How the work went
- The local model wrote `hx-on::click` (htmx 2 reads it as `htmx:click`, which never fires) and patched over it with a page-wide click listener. The escalation added a test that fails any template using `hx-on::` with a browser event, so this mistake can't come back.
- The runner's refusal was tested for one of the three "up" states. The review now tests all three.

### 9. What clogged the factory line
- f273-02 spent about 2 h 30 min on the local model (17:07–19:35: a timeout, then two failed attempts) before the lead finished it in 19 minutes for $2.25. Its two sibling tickets that day went the same way: see the second Factory suggestion in item 6.

<!-- runner report -->
<!-- runner report -->
