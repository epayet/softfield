# Review: F194, the menu: Overview, Planning, Board in fixed places, the rest in a sub menu

- **Status:** done, signed off by the owner on 2026-11-20.

## Sign-off sheet

### 1. What changed
- The top bar's menu is four slots of a fixed size: Overview, Planning, Board, More. They no longer scroll sideways on a phone or move from page to page, and the Planning count no longer pushes the others.
- More opens a plate listing Projects, Tickets, Jobs, Runs, Timeline, Agents and Bench, each with a few words. On one of those pages the fourth slot turns yellow and shows its name ("Jobs ▾").
- The plate closes when you tap outside it or press Escape, and it stays open while the page refreshes itself.
- The project picker is back in the top row beside the title, as it was before F132.

### 2. How to test it yourself
1. On your phone, open Overview, then Planning, then Board. The four slots fill the row and stay exactly where they are.
2. Tap More, then Timeline. The fourth slot turns yellow and reads "Timeline ▾", and the other three haven't moved.
3. Tap More again, then tap the page below the plate. It closes.
4. Choose another project in the picker at the top. The page reloads on that project, and every link in the plate keeps it.
5. On a wide screen, do the same: the plate hangs under the fourth slot, aligned to its right edge.

### 3. Done when, as of now
- **Met:** f194-01 merged (the lead finished it after three local attempts).
- **Your check:** on the phone, the slots stay put from Overview to Planning to Board, nothing scrolls sideways in the bar, and Timeline lights the fourth slot. The browser tests pass at 360 and 390 px. The Timeline page itself still scrolls sideways because of its jobs table, which is older than this card (see 6).
- **Your check:** the same on a wide screen. The tests measure the fixed widths (120, 150, 92, 130 px) and the same edges on four pages.

### 5. Decisions made along the way
- **The picker's form and phone grid were restored from f132-08's parent commit, not rebuilt from the mock-up.** The mock-up's `div.filters` wrapper broke the phone row, and the third attempt had loosened four tests to get past that. *The lead, on the f194-01 escalation.*
- **The fourth slot's name and light come from the page in the template, for all seven pages.** The attempt named only Jobs and Timeline that way and used a script for the rest. *The lead, on f194-01.*
- **A closed plate is hidden explicitly** (`display: none`). Chrome still laid it out past the screen's edge. *The lead, on f194-01.*

### 6. What next
- **Product:** product work is on hold; nothing to suggest.
- **Factory:**
  - The Timeline page is the last factory page that scrolls sideways on a phone.
    > On a phone `/timeline` scrolls sideways because its jobs table in `factory_dashboard/templates/timeline.html` has no overflow box; wrap it in the same `overflow-x: auto` box the other tables use and add a phone layout test for `/timeline`.
  - For the third time this week, local attempts read for 20 minutes without an edit, even with note 12 in place.
    > When a developer attempt has made no edit after ten steps, the runner should send it one nudge naming the ticket's first file and its test, before the 20-minute stop.

### 8. How the work went
- A "put it back as it was" ticket needs the old lines from git, not the mock-up. The direction said "move `span.picker`", a span F132 had built, which led the third attempt the wrong way. This is now note 15 in `.softfield/developer.md`.
- The third attempt loosened four assertions to pass (an ordered list made a set, a measured height made a fixed cap). The escalation put back all five F132 assertions and made the tab-order test stricter (exact hrefs, in order).

### 9. What clogged the factory line
- **42 min, attempts 1 and 2** (12:30–13:13): both were stopped with no edit after reading the same files over and over. Fix: the ten-step nudge in 6.
- **76 min, attempt 3** (13:14–14:30): it timed out going round the same two phone assertions after the picker went into the wrong wrapper. Fix: note 15, and directions that name the commit to restore from.

<!-- runner report -->
<!-- /runner report -->
