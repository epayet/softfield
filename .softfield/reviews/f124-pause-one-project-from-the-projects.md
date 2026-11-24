# Review: F124, Pause one project from the Projects page

**Status:** round 1 done, ready for your sign-off (one fix ticket, f124-04, is queued).

### 1. What changed
- Each project on the Projects page has its own Pause / Resume. A paused project finishes the job it is on, then runs no ticket, checkpoint or review, while its planning room still answers you; the other projects carry on.
- A paused project's plate shows a hazard edge and "Paused by you since HH:MM"; the Overview's Next in line gives it one line instead of listing its tickets. In the terminal, `softfield` and `softfield run --dry-run` say "paused by you". The top bar's Pause still holds the whole factory.

### 2. How to test it yourself
1. On the Projects page, press Pause on coucou: the button turns dashed orange "Pausing…" at once, with the "On its way" line.
2. After the runner's next pick, reload the page: coucou's plate shows the hazard edge, "Paused by you since HH:MM" and Resume (until f124-04 merges, the plate doesn't redraw by itself).
3. On the Overview, Next in line shows "coucou · Paused by you since HH:MM: its tickets wait." and none of coucou's tickets; softfield's tickets keep running.
4. Write a message on one of coucou's cards: the lead answers it.
5. Press Resume: after the next pick, coucou's tickets are picked again.

### 3. Done when, as of now
- **Met:** f124-01, f124-02 and f124-03 are merged (f124-03's Next in line fixed by the review).
- **Your check:** the Projects page steps above, on your phone; no project has been paused on the live line yet, so the tests are all that has run it.
- **Met:** `softfield run --dry-run` says a paused project's tickets are "paused by you", and a bare `softfield` lists it "paused by you since HH:MM" (both tested).

### 5. Decisions made along the way
- **The paused line names its project and shows even when nothing else waits.** f124-03's line named no project, and the Queue said "The queue is empty." when the paused project held the only tickets. *The review.*
- **A paused project's plate redraws by itself once the runner takes the request (f124-04).** D5 stopped at "on its way until the runner finishes it", which left "Pausing…" on screen until a reload. *The review.*

### 6. What next
- **Factory:** once f124-04 merges, try a pause on the phone during a long softfield run to see that only that project's line holds.

### 8. How the work went
- The local model's f124-03 passed its own tests but missed its goal: the paused project in its tests had no tickets, so nothing showed that its tickets were still listed. A test that checks something is left out needs that thing in its fixture; the review rewrote the tests on the shared `write_other` fixture.
- f124-02 took three local attempts (about two hours) before the lead finished it in 8 minutes: the model kept changing the protected `ask` response to draw "Pausing…". The lead added the pattern (drawn by the button's own `hx-on::before-request`) to `.softfield/developer.md`.

### 9. What clogged the factory line
- f124-02: three failed local attempts, 07:14 to 14:30 with a gap, on the same protected-file trap; fixed by the developer note above.

<!-- runner report -->
<!-- /runner report -->
