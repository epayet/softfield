# Review: F77, allowance bars the same length on the Overview and the same colours on every page

## Sign-off sheet

### 1. What changed
- **Overview, Agent allowance:** Claude's 5-hour, Claude's week and Copilot's month now sit in equal columns, so their bars are the same length. Before, the Fast lane line under Claude's meters pushed Copilot's month onto a row of its own, as wide as the panel.
- **Planning, the lead's window:** both bars are now drawn by the same piece of template as the Overview's. A reading above 95% is red there too (it used to stay yellow), and the yellow and green follow the same rule on both pages.
- The phone layout (one row per window) is unchanged.

### 2. How to test it yourself
1. On the laptop, open the Overview at full width. The three allowance bars should be exactly the same length, with or without the Fast lane line showing.
2. On the phone, open the Overview: each window should still be one row, as before.
3. When Claude's 5-hour window is above 95%, open `/planning` and the Overview side by side: the bar should be red on both. Past the mark it should be yellow on both, and under it green on both.

### 3. Left for later
- The planning tile's week bar has no pace tick (the Overview's has one). Only the fill colour was in scope, so I left it as it is (F2 below).
- No bug tickets set aside.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-10 to 11, [session 18:27](../sessions/2026-11-10-1827.md) and [session 06:20](../sessions/2026-11-11-0620.md): f77-01 failed three local attempts (two stopped with no edit after 20 minutes, then `tests-fail-on-main`). The lead finished it on its branch (Opus, about $1.25 for the direction and the finish).
- 2026-11-11, [session 08:33](../sessions/2026-11-11-0833.md): f77-02 was merged by the local model on its second attempt. The first attempt timed out after 79 minutes. Claude cost nothing.
- The lessons that mattered:
  - **The ticket blamed the wrong cause.** It blamed the "use reserve" lever, but the real cause was the Fast lane line. So the developer's test used data where the bars were already equal, and it could never fail on main. This is now note 10 in `.softfield/developer.md`: run a layout test once against the old rule.
  - **The local model met the letter of the ticket, not the point.** For f77-02 it only re-spaced the existing tests and never tested the red-on-Planning case. I added that test in review (F1).

### 6. What next
- **Product:** product work is on hold (owner, 2026-10-04).
- **Factory:**
  - When a developer ticket's Done when names concrete readings (97% → red), its tests should check them. The f77-02 gates passed without them, because "fail without the change" was met by re-spaced regexes. F61 had the same gap.
  - Have the planner name a test for each reading, and have `check-tickets` hold to it (text to plant under "Factory" below).

### 7. What clogged the factory line
From the metrics database (jobs for the two tickets):
- **About 9 hours parked:** f77-01 waited from 21:35 on the 10th to 06:45 on the 11th for Claude's reset before its direction could run. *To unclog it:* reserve-aware ordering already exists. The direction cost $0.60 and took 1 minute, so it is a candidate to run under the planning reserve.
- **About 70 minutes of failed local attempts on f77-01** (26.5, 20.1 and 23.4 minutes). Two stopped with no edit, and the last one failed only because its test drew equal bars on main. *To unclog it:* a ticket that names a layout cause checks it on real data first (note 10).
- **79 minutes lost when f77-02's first attempt timed out.** *To unclog it:* nothing specific. The second attempt passed in 26 minutes.

---

<!-- runner report -->
<!-- /runner report -->

## What was built
- **f77-01** (`56aecf2be`, finished by the lead): `.allow` became `display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))`, and `.cards-on` became `grid-column: 1 / -1`. `.allow > div` keeps `flex: 1 1 180px` for the phone's flex column. A browser test at 1440 px uses the Fast lane fixture and checks every `.meter` is within 1 px of the others.
- **f77-02** (`1da13f917`, local model):
  - `_partials/allowance_bar.html`, the macro `allowance_bar(a, pace=none)`, holds the fill rule, the "ahead" span, the pace tick and the mark.
  - `allowance.html` and the planning tile both import it.
  - The planning tile's 75% fallback mark was dropped as specified: `planning()` always finds both Claude rows, and the no-reading test still passes.
  - The planning mark's title is now the window's `mark_label` ("kept for you from here"), which says the same thing.

## Findings
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | f77-02's Done when had no test: nothing checked that 97% is red on `/planning` or that the rule lives only in the macro. The developer only re-spaced two regexes. | Fixed: `test_the_lead_window_colours_a_reading_as_the_overview_does` (97/80/40%, checks the planning tile and the Overview's 5-hour) and `test_no_page_keeps_its_own_allowance_fill_rule` in `tests/factory_dashboard/test_planning.py`. The 97% case fails on the old template. |
| F2 | nit | report | The planning tile's week bar is drawn without the pace tick (`allowance_bar(week)` gets no `pace`). | Left as it is: the colours match, and the pace is the Overview's story. |
| F3 | nit | report | f77-02's Done when said no template may hold the class words, but the Overview's legend needs them for its swatches. | This was the lead's wording, not the developer's error. The new test checks Jinja expressions only. |

Checkpoints: none ran on this milestone, so there is nothing to confirm or mark missed. **Score: 8/10.** The code is right and small. f77-01 needed the lead, and f77-02's tests were thin.

## French
No user-facing French changed (factory pages only).

## Factory
- **Flow:**
  - f77-01 was escalated after three attempts, and Claude's 5-hour window parked it overnight.
  - f77-02 passed on its second local attempt.
  - The owner didn't need to step in, and nothing stopped for an ADR.
- **Models:**
  - The local model (qwen3.6-35b-a3b) did f77-02 alone, using 6.05M tokens in.
  - On f77-01 it got the CSS right by its third attempt, but its test couldn't fail on main.
  - Opus spent about $1.25 on f77-01, for one direction and one finish.
- **What to change:** Done-when cases with no test are now a recurring way local tickets pass thin (F61's review found the same).
  - A finding that recurs becomes a check. My suggestion is that the planner names a test for each concrete reading in a developer ticket's Done when, and `softfield check-tickets` refuses a ticket with a reading but no named test.
  - That is runner code (protected), so here it is as text ready to plant: *"check-tickets: a developer ticket whose Done when gives concrete readings (97% → red) names the test that checks each one; F61 and F77 both passed the gates with those readings untested."*
