# Review: F262, Archive a project: off the picker, its tickets wait, unarchive any time

**Status:** review done after round 2: ready for your sign-off. The fix ticket f262-04 is merged, and the review fixed what it broke.

### 1. What changed
- Each project on the Projects page has an Archive button at the foot of its plate. An archived project leaves the project picker, the top bar's status, the ordered list and the Overview's lanes and floor. It sits in a folded "Archived · N" bay under the list, with its Planning and Board links and an Unarchive button.
- The runner takes none of an archived project's tickets, checkpoints or reviews, but its planning still goes on and anything it has waiting for you still shows in Needs you. Unarchive brings it back, running, at the bottom of the list.
- Once the runner takes an Archive or an Unarchive, the page moves the project between the list and the bay by itself, with no reload. It doesn't when you've typed a new order and not sent it, so your order isn't lost.
- In the terminal, `softfield run --dry-run` says its tickets are "archived", and a bare `softfield` lists it "(archived)".
- Matches the mock-up, except that the archived line says "Archived by you." with no date.

### 2. How to test it yourself
1. On the Projects page, on your phone, press Archive on coucou: it turns dashed orange "Archiving…" at once, with the "On its way" line.
2. Leave the page open. After the runner's next pick, coucou leaves the list by itself and "Archived · 2" under the list holds it beside waifu-gallery. The page shows only one top bar and one Start a project.
3. Open the bay, then coucou's Board from there: its cards are as they were. On the Overview, coucou's tickets aren't in the Queue.
4. Press Unarchive on coucou. After the next pick, it comes back last in the list, and back in the picker.
5. Then change a place number: Send new order lights up and sends.

### 3. Done when, as of now
- **Met:** f262-01, f262-02, the stretch f262-03 and the fix f262-04 are merged; Archive and Unarchive redraw the page without a reload (tested in a browser).
- **Your check:** the Projects page steps above, on the live line. waifu-gallery was archived there on 24 Nov and reads right.
- **Met:** `softfield run --dry-run` says an archived project's tickets are "archived" (tested); a bare `softfield` lists it "(archived)" (from the code: the guide prints the stored word).

### 5. Decisions made along the way
- **Unarchive moves the project last by itself.** Before, it only came back last if you'd sent a new order while it was archived; waifu-gallery would have come back third. *The review.*
- **The archived line has no date.** The mock-up said "Archived by you on Tue 17 Nov", but archiving stores only the word "archived" and no time, and a new column for a date wasn't worth it. *f262-02.*
- **The stretch's floor keeps an archived project while one of its jobs still runs.** That way a job that is running when you archive doesn't vanish halfway; Needs you, the timeline and the history keep every project. *f262-03.*
- **After an archive, the whole Projects list is redrawn, not one plate.** The plate moves between the list and the bay, which may appear or go, so the order script now finds its form each time instead of keeping the first one. *The review, on f262-04.*

### 6. What next
- **Factory:**
  - The local model failed or timed out on both of its F262 tickets, and each time a third attempt ran for the full 75 minutes after Claude's direction before Claude finished it in under 20.
    > After a direction, if the local model's third attempt on a ticket times out, stop giving local attempts to tickets that already failed twice with a browser test, and hand them to Claude straight away.
  - f262-04 passed its own tests while a second copy of the whole page sat inside the Projects section, because the tests only looked inside the redrawn part.
    > A browser test that redraws part of a factory page should also check that the page's main sections appear only once, through a shared test helper, so a swap without `select` fails at once.
  - > The Archived bay could say when each project was archived and since how long its tickets have waited, so I can tell which ones to forget.
  - > Simpler: in `factory_dashboard/overview.py`, `_live_context` rebuilds the archived set that `on_the_floor` already builds: have `on_the_floor` return it too, and drop the second comprehension (about 3 lines).

### 8. How the work went
- f262-03 first narrowed `every_project`, the helper the timeline and the history read too, then had to undo that with a second helper. The note now in `.softfield/developer.md` says to grep a shared helper's callers before changing what it returns.
- A test helper that filtered out the new request kind cost f262-02's last local attempt its whole session; the developer note on request buttons now names that trap.
- f262-04 left out the `select` its ticket asked for, and its tests couldn't see the result. The review added the "appears once" checks to both redraw tests and suggests a shared helper in 6.

### 9. What clogged the factory line
- f262-02: 2 h of local attempts (two failures, then a 75-minute timeout after the direction) before Opus finished it in 19 minutes.
- f262-03: 2 h 20 min of local attempts the same way (68 minutes of failures, then a 75-minute timeout) before Opus finished it in 12 minutes. The fix is the first Factory suggestion in 6.

<!-- runner report -->
<!-- /runner report -->
