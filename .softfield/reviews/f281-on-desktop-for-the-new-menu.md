# Review: F281, every page in one row on a wide screen

- **Status:** done, signed off by the owner on 2026-11-27.

**Status:** round 1 passed, no fixes needed; ready for your sign-off.

### 1. What changed
- On a laptop or desktop the top bar now shows every page in one row: Overview, Planning, Board, a striped seam, then Projects to Bench. More is gone at full width.
- On a narrower window, pages leave the row from Bench backwards and More comes back holding only those pages. On the page you're on, its own slot turns yellow; More names it only while it holds it. The phone's four slots haven't changed.
- Matches the mock-up.

### 2. How to test it yourself
1. On the desktop at full width, open the dashboard. The row reads Overview, Planning, Board, a striped seam, then Projects, Tickets, Jobs, Runs, Timeline, Agents, Bench, with no More.
2. Open Timeline: its slot turns yellow and nothing in the row moves. Hover Jobs: it says "every job an agent ran, newest first".
3. Narrow the window slowly. Bench and Agents leave together, then Timeline, Runs and so on, and More comes back. At about 900 px, More lists Timeline, Agents and Bench only.
4. At about 900 px, open Timeline: More turns yellow and reads "Timeline".
5. On the phone: the four slots and More, as before.

### 3. Done when, as of now
- **Met:** f281-01 is merged, and the tests check full width, the steps and the 900 px case (731 dashboard tests pass).
- **Met:** the row at full width, Timeline lighting its own slot, Jobs' hover words, and More listing only the pages that left the row. The after pictures and the tests both show these.
- **Your check:** narrowing the window in a real browser, and the phone as today.

### 5. Decisions made along the way
- **Two labels in More's slot, one hidden at each width.** The slot shows the page's name while that page is in More, and "More" once it's back in the row, with no script. *The lead, on f281-01.*

### 6. What next
- **Factory:**
  > On a wide screen, make the Planning slot's count a small badge that shows only when something needs me, so the row stays calm.

### 8. How the work went
- The local model edited only the page template and never the stylesheet (the CSS file), across three attempts; two of them read for 20 minutes without an edit. The developer notes now name the CSS block and say to make the first edit there.

### 9. What clogged the factory line
- f281-01 sat parked on 25 Nov waiting for Claude's reset before its direction and its finish. Fix: run the escalation earlier while Claude has room (ADR 20's reserve).

<!-- runner report -->
<!-- runner report -->
