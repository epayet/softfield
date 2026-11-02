# Review: F82, text boxes grow with what you type

- **Status:** done, signed off by the owner on 2026-10-29.

## Sign-off sheet

### 1. What changed
Every text box on the dashboard now grows as you write: the Plant box first, plus a waiting plant's edit, the reply on a card's thread and the comment under a key point. It grows line by line until it fills about 60% of the screen, and only then scrolls inside. It never starts smaller than before, and it shrinks back when you clear it or send a plant. A box that the page fills for you (Try again on a refused note, or editing a waiting plant) fits its text as soon as the cursor is in it.

### 2. How to test it yourself
1. On the phone, open Planning and type a long idea in the Plant box, with several returns: the box gets taller with each line, and nothing scrolls inside it.
2. Keep typing (paste a long text if quicker) until the box reaches about two thirds of the screen: it stops growing there and scrolls inside.
3. Clear it: it goes back to its usual four lines.
4. Type a few lines and press Plant: the new, empty box is back at four lines.
5. On a card's thread with a proposal, tap a key point to comment and write several lines: that box grows the same way.
6. If a plant is ever refused, press Try again: the box opens with your words and fits them.

### 3. Left for later
Nothing deferred, and nothing new in `docs/backlog.md`.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-26: Opus wrote the plan and the ticket ($0.78).
- 2026-10-27 (run 20261027-005355, which left no session report; its parks show in [this session](../sessions/2026-10-27-2258.md)): the local model's first attempt was right, but failed the whole-suite gate on a test that main itself failed. The second attempt stopped after 20 minutes with no edit. The ticket then waited about 18 hours parked for a Claude direction.
- 2026-10-28 ([session](../sessions/2026-10-27-2319.md)): an Opus direction ($0.47), then the local model's last attempt passed and merged. A Claude checkpoint flagged one loose test (a nit).
- Review, 2026-10-28: fixed the focus half of the script, which crashed on every focus, and tightened two tests.
- Lessons:
  - The local model copied the typing handler for focus and changed one line, which broke it. No test pressed focus because the ticket named that path only in its context, not in its Done when. Now in the Known range: each path the plan names gets its own Done when line.
  - Twenty minutes of a good first attempt and about 18 hours of park went to a red main, the same trap as F80. f80-02, merged this week, now lets a developer's attempt that only fails on main's own tests wait without being counted.
  - The checkpoint judged the tests and missed the crash, which was plain in the 16-line diff. That's the same pattern as F68 and F69.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:**
  - Watch whether f80-02 ends the "red main burns a good attempt" pattern. F80 and F82 both lost a day to it.
  - The browser step for checkpoints, suggested after F68 and F69, would have caught this crash at once (any page error on focus). If you want it, text to plant: "A checkpoint on a page ticket clicks through its Done when in a browser, watches for page errors, and says what it saw."

### 7. What clogged the factory line
- **Parked for a Claude direction: about 18 hours** (2026-10-27 08:58 to 10-28 02:49). The cause was a red main, not the work. To unclog it: f80-02 (done), which spares the attempt and waits for main.
- **Failed attempts: about 51 minutes** (attempt 1, 31 min, right but failed on a red main; attempt 2, 20 min, no edit). To unclog it: the same f80-02.
- **Waiting before the start: about 17 days** (planted 2026-10-09; the plan was parked on 10-23 because Claude was limited, then written on 10-26). To unclog it: nothing. The board's order put it there.
- No waits for you on this card.

## What was built
- `factory_dashboard/templates/base.html`: one handler, `fitBox`, on `input` and `focusin` for any `textarea` on any page. It sets the height to `auto`, then to `scrollHeight` plus the borders, which is correct because `dashboard.css` sets `box-sizing: border-box` for everything. A box's `rows` stays its smallest height, because `auto` falls back to it.
- `factory_dashboard/static/dashboard.css`: `textarea { max-height: 60vh; overflow-y: auto; }`.

Tests (`tests/factory_dashboard/test_planning.py`, Playwright): the Plant box grows over ten typed lines with no inner scroll; it stops at 60% of an 800 px window and scrolls; emptying brings it back; a sent plant's fresh box starts at four rows; a key point's comment box grows the same way. The review added a box filled by a script that fits on focus, with no page error. The session report lists `test_planning.py` as an edited test file, but f82-01 only added tests at the end: no existing test changed.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | The focus listener made `ta` a boolean (`tagName === "TEXTAREA"`) and threw on every focus, so a box filled by Try again or a pre-filled edit never fitted until the first key | Fixed: one `fitBox` handler for both events, using `closest("textarea")`. A new test sets the value by script, focuses, and checks it grew with no page error; it fails on the old code |
| F2 | nit | claude | The emptied-box and fresh-box tests accepted any height at or above the start, so a box that stayed tall passed | Fixed: both assert the starting height, within 1 px |

Checkpoint verdicts: C1485-3 confirmed (the fresh-box test's `>=`; the emptied-box test had the same gap, and both are fixed as F2). F1 was missed: the broken line was in the 16-line diff the checkpoint read.

Score: 7/10. This was a small, well-planned ticket, and the local model got the mechanism, the CSS and the main tests right on its first attempt. It lost points for a half that crashed on every use, and a day of waiting on a red main.

Checked and fine: `scrollHeight` plus the borders is exact under the global `border-box`. Boxes redrawn by htmx start at their `rows`, as the plan said. `liveIdle` and the comment counters on the thread and proposal pages are untouched. The tap-to-comment focus on a thread (f23-01) now fits the box too.

Tests: the eight text-box tests pass after the fix, and the new one fails without it. Ruff is clean on the edited file. The full `tests/runner tests/factory_dashboard` run hit this job's 10-minute background limit and was stopped at about 98%, with nothing failed (the `E`s printed as it was killed). The last five files on their own (`test_reports` to `test_timeline`) pass: 135 tests. The runner's gates run the whole suite before any merge. The rest of this diff range belongs to other milestones (F38, F68, F69, F80, F84, F164 and others) and their own reviews.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Nothing new.

## Factory
- Flow: one developer ticket by the local model in three attempts, with an 18-hour park for one Opus direction. One Claude checkpoint, with one nit. No stops for you, no limits hit during the build. The plan itself had waited on Claude's limit on 10-23.
- Models: Qwen3.6 35B, about 1.4 hours of model for 16 lines of script and a CSS rule. It was right first time apart from the copied focus handler. Opus: $0.78 for the plan, $0.47 for the direction.
- What to change: the Known range now says to give each path the plan names its own Done when line. f80-02 covers the red-main park. The browser step for checkpoints is in 6, for you to plant if you want it.

<!-- runner report -->
<!-- /runner report -->
