# Review: F256, the top bar on a wide screen: one line, one height, edges matched

**Status:** reviewed, round 1. No blocking or should-fix findings; ready for your sign-off.

### 1. What changed
- On a computer, the top bar's top row is one straight line: the logo, the dot, the words, ⏸, the "On" plate, the project picker and the switch share one centre, and the controls are all 36 px tall.
- The project picker is now a plate like the "On" plate: "PROJECT", then the name. The logo starts where the yellow stripe starts, and the switch ends where it ends.
- In a narrower window (640 to 1000 px) the row stays on one line and the status words end in "…". The phone's bar looks as before, and its picker still shows only the name.
- Matches the mock-up (the address beside the logo is in a small framed box, as in the mock-up's Proposed).

### 2. How to test it yourself
1. On the computer, open the Overview: the logo, the dot, the words, ⏸, "On", the project picker and the switch sit on one line, their tops and bottoms matching.
2. Check that the logo's left edge and the switch's right edge line up with the two ends of the yellow stripe below them.
3. Narrow the window to about 760 px: the row stays one line and the words end in "…". Hover the dot to read the whole sentence.
4. Flip to the light theme and look again: the same.
5. On the phone, the bar looks as it did, and choosing another project in the picker reloads the page with it.

### 3. Done when, as of now
- **Met:** at 1440 and 1000 px, in both themes, the parts share one centre and the controls one height (measured by `test_at_1440px_and_1000px_the_top_row_is_one_line`).
- **Met:** at 1440 px the crate and the switch meet the stripe's two ends, within 1 px.
- **Met:** at 760 px the row is one line and the words end in "…", with the dot's title still holding the whole sentence.
- **Met:** at 390 px the bar is no taller than before, and the picker shows only the project's name.
- **Met:** choosing a project reloads the page with it. The listed tests pass, and the gates passed at merge.
- **Your check:** the look on your own desktop, in both themes (steps 1 to 4).

### 5. Decisions made along the way
- **The picker's new look applies only inside the top bar (`.bar-top .filters`), not to every `.filters`.** The Tickets and Jobs pages use the same class for their own form, and changing it everywhere made those pages scroll sideways on a phone. *The lead, on f256-01.*

### 6. What next
- **Product:** product work is on hold.
- **Factory:** the local model lost all three attempts on this ticket to a class shared by other pages. The developer notes now say to search the templates before restyling a class (developer.md note 13).

### 8. How the work went
- The local model made the top bar right but restyled `.filters` everywhere, which broke two phone tests on `/tickets`. It spent three attempts failing on those tests, and then the lead finished the ticket on its branch. The lesson is now in developer.md note 13.

### 9. What clogged the factory line
- f256-01 failed its gates three times on the same two tests (`task-tests`, the page scrolling sideways on `/tickets`) before it reached the lead. The fix is the developer note above.

<!-- runner report -->
<!-- /runner report -->
