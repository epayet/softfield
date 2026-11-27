# Review: F262, Archive a project: off the picker, its tickets wait, unarchive any time

**Status:** round 1 done; one fix ticket, f262-04 (the page redraws itself once the runner takes Archive or Unarchive), is queued for round 2.

### 1. What changed
- Each project on the Projects page has an Archive button at the foot of its plate. An archived project leaves the project picker, the top bar's status, the ordered list and the Overview's lanes and floor. It sits in a folded "Archived · N" bay under the list, with its Planning and Board links and an Unarchive button.
- The runner takes none of an archived project's tickets, checkpoints or reviews, but its planning still goes and anything it has waiting for you still shows in Needs you. Unarchive brings it back, running, at the bottom of the list (the review's fix: it used to go back to its old place).
- In the terminal, `softfield run --dry-run` says its tickets are "archived", and a bare `softfield` lists it "(archived)".
- Matches the mock-up, except the archived line says "Archived by you." with no date, and the button stays "Archiving…" until you reload (f262-04 fixes that).

### 2. How to test it yourself
1. On the Projects page, on your phone, press Archive on coucou: it turns dashed orange "Archiving…" at once, with the "On its way" line.
2. After the runner's next pick, reload: coucou is gone from the list and the picker, and "Archived · 2" under the list holds it beside waifu-gallery.
3. Open the bay, then coucou's Board from there: its cards are as they were. On the Overview, coucou's tickets aren't in the Queue.
4. Press Unarchive on waifu-gallery. After the next pick, reload: it is last in the list and back in the picker.

### 3. Done when, as of now
- **Met:** f262-01, f262-02 and the stretch f262-03 are merged; f262-04 (redraw without a reload) is queued.
- **Your check:** the Projects page steps above. waifu-gallery was archived on the live line on 24 Nov and its result reads right; until f262-04 merges you need to reload after the runner's pick.
- **Met:** `softfield run --dry-run` says an archived project's tickets are "archived" (tested); a bare `softfield` lists it "(archived)" (from the code: the guide prints the stored word).

### 5. Decisions made along the way
- **Unarchive moves the project last itself.** Before, it only came back last if you'd sent a new order while it was archived; waifu-gallery would have come back third. *The review.*
- **The archived line has no date.** The mock-up said "Archived by you on Tue 17 Nov", but archiving stores only the word "archived", and no time; adding a column for a date wasn't worth it. *f262-02.*
- **The stretch's floor keeps an archived project while one of its jobs still runs.** That way a job running when you archive doesn't vanish halfway; Needs you, the timeline and the history keep every project. *f262-03.*

### 6. What next
- **Factory:**
  - The local model failed or timed out on both of its F262 tickets, and each time a third attempt ran for the full 75 minutes after Claude's direction before Claude finished it in under 20.
    > After a direction, if the local model's third attempt on a ticket times out, stop giving local attempts to tickets that already failed twice with a browser test, and hand them to Claude straight away.
  - > The Archived bay could say when each project was archived and since how long its tickets have waited, so I can tell which ones to forget.
  - > Simpler: in `factory_dashboard/overview.py`, `_live_context` rebuilds the archived set that `on_the_floor` already builds: have `on_the_floor` return it too, and drop the second comprehension (about 3 lines).

### 8. How the work went
- f262-03 first narrowed `every_project`, the helper the timeline and the history read too, then had to undo that with a second helper. The note now in `.softfield/developer.md` says to grep a shared helper's callers before changing what it returns.
- A test's helper that filtered out the new request kind cost f262-02's last local attempt its whole session; the developer note on request buttons now names that trap.

### 9. What clogged the factory line
- f262-02: 2 h of local attempts (two failures, then a 75-minute timeout after the direction) before Opus finished it in 19 minutes.
- f262-03: 2 h 20 min of local attempts the same way (68 minutes of failures, then a 75-minute timeout) before Opus finished it in 12 minutes. The fix is the Factory suggestion in 6.

<!-- runner report -->
<!-- /runner report -->
