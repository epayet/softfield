# Review: F69, a button to switch between light and night

- **Status:** review round 1 done: every finding is fixed in the review, waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
Every dashboard page has a button at the right of the top bar. It names the theme it switches to: "Light" while the night theme shows, "Night" while the light one shows. Pressing it switches the whole page at once (the colours, the factory floor and the charts) without reloading. Each device remembers its own choice: the phone and the laptop can differ. Until you press it on a device, that device's pages follow its own light or dark setting, as before. On the phone the button sits on the same row as the title, the status dot and the project picker, so the top bar is no taller.

### 2. How to test it yourself
1. On the laptop, open the Overview. Top right, beside the project picker: "LIGHT". Press it: the page turns pale at once, and the button now says "NIGHT".
2. Open Milestones: the page is already light, and its charts are drawn in the light colours. Press "Night": the charts change colour where they are, with no reload.
3. Reload, then open the Board: both stay in the theme you chose.
4. On the phone, open the dashboard: the button shares the top row with "SoftField", the status dot and the project picker. It is easy to tap and the top bar is no taller. Press it: the phone keeps its own choice, separate from the laptop's.
5. On a device where you haven't pressed it (a private window will do), switch the system between light and dark: the page follows. Then press the button and switch the system again: the page now keeps your choice.

### 3. Left for later
- A three-way choice (device / light / night): you agreed to the two-way button in the plan. If you ever want "follow my device" back on a device where you pressed it, clearing the site's data does it today. Nothing filed.
- Nothing new in `docs/backlog.md`.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-17 ([session](../sessions/2026-10-17-0017.md)): the local model built f69-01 on its second attempt (the first timed out at 78 minutes). The Copilot checkpoint, standing in for Claude, filed f69-02 (a system change left the button saying the wrong word and the charts in the old colours) and f69-03 (weak tests). Both merged the same night.
- 2026-10-17 ([session](../sessions/2026-10-17-1300.md)), 2026-10-23 ([session](../sessions/2026-10-23-1549.md)): f69-04 and f69-05, again on the same tests, each filed by a stand-in checkpoint.
- 2026-10-24 to 2026-10-27 ([session](../sessions/2026-10-26-2252.md), [session](../sessions/2026-10-27-2319.md)): f69-06 failed twice (no edit in 20 minutes), waited about three and a half days parked for Claude's direction, then failed twice more and passed on the fifth try.
- Review, 2026-10-28: fixed a system change that overrode your stored choice, belt labels on the floor that had lost their dim colour in the night theme, the phone button's small tap target, and a small chart leak. I also wrote the two tests the fix chain never got right myself.
- Lessons:
  - Four fix tickets (f69-03 to f69-06, about 3.6 hours of local model plus the park) polished the same two tests and still never proved the thing they were named for: the chart test loaded a new page instead of watching a chart redraw, and the height test compared dark with light. f68-08, which landed this week, now sends a fix of a fix to the lead. This chain ran before it existed.
  - The CSS leak came from a mechanical edit (media query to attribute selector) on a rule with a comma. It is now a check: every light rule's selectors must each name the light theme.
  - No checkpoint caught the stored-choice bug, the leak or the 22 px button, though all three were in diffs they read. Like F68, each checkpoint reviewed the newest test and none opened the page as a user.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:**
  - Watch whether f68-08 ends the fix-of-a-fix chains: F69 is the third card in a row (after F114 and F68) where a checkpoint's test finding turned into three or more developer tickets.
  - F68's suggestion still stands and would have caught this card's misses: a checkpoint on a page ticket opens the page in a browser and presses what the Done when names. Text to plant if you agree: "A checkpoint on a page ticket clicks through its Done when in a browser, and says what it saw."

### 7. What clogged the factory line
- **The fix chain on two tests: about 5.6 hours of local model** (f69-02 to f69-06, 2026-10-17 to 10-28). f69-02 fixed a real bug; the other four were about tests. To unclog it: f68-08 (done). A fix of a fix now goes to the lead.
- **f69-06 parked: about 3.8 days** (2026-10-24 00:31 to 10-27 19:23), waiting for Claude's direction after two attempts with no edit. To unclog it: the same f68-08; the lead would have taken it first.
- **Failed attempts: about 2.5 hours** (f69-01's 78-minute timeout, f69-06's four stops). To unclog it: nothing more. f69-01 passed next, and f69-06's cause is covered above.
- **Waiting before the start: about 8 days** (planned 2026-10-09, first job 10-17), behind F68's brand tests and F17's top-bar row, both on the same lines of `base.html`. To unclog it: nothing. The order was right, since both changed the same row.
- No waits for limits or for you on this card.

## What was built
- `factory_dashboard/templates/base.html`: an inline script in `<head>` sets `data-theme` on `<html>` from `localStorage["theme"]`, else from the system. While nothing is stored, it follows a live system change, updates the button and fires `themechange` (f69-02). The review added a check: the system is ignored once a choice is stored. The `#theme-btn` button flips `data-theme`, stores it, fires `themechange` and relabels itself.
- `factory_dashboard/static/dashboard.css`: both light blocks key on `:root[data-theme="light"]`; no `prefers-color-scheme` is left. `.theme-btn` uses the display type, uppercase, in ink-2. On a phone it takes the fourth column of the top row (44 px tall since the review).
- `factory_dashboard/static/charts.js`: each drawn chart keeps its instance (and, since the review, its resize observer). On `themechange`, `redrawAll` disposes them and draws again with the new tokens.

Tests (`tests/factory_dashboard/test_app.py`): the button on every page, its words and titles in each theme, pressing it changes the tokens, the choice persists across reload and pages, a page with nothing stored follows the system and a live change (button and event), the bar's height at 390 px. Edited existing test, reviewed: `test_dark_is_the_default_and_light_follows_the_system` now reads the `:root[data-theme="light"]` block and asserts no `prefers-color-scheme` is left. That's faithful to the ticket, though its name still says "follows the system". Review additions: a drawn chart redraws in place (fill #7aa7ff to #3f6fd6 on the same load, one chart), the bar with and without the button at 390 px plus the 44 px target, a stored choice survives a system change, and every light rule is scoped.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | A system theme change undid the button's stored choice on a page that loaded with nothing stored | Fixed: the listener returns when a theme is stored; new test |
| F2 | should-fix | claude | `.floor .belt text` lost its theme scope, so night-theme belt labels turned ink-2 instead of muted | Fixed; a test checks every light rule's selectors |
| F3 | should-fix | claude | The tests never proved a chart redraws in place or that the button adds no height | Fixed by rewriting both tests (done by the lead: four developer tickets had already failed at it) |
| F4 | should-fix | claude | The phone button was about 22 px tall, under the row's 44 px targets | Fixed: `min-height: 44px` in the phone block; asserted |
| F5 | nit | claude | Every redraw left a ResizeObserver resizing a disposed chart | Fixed: observer disconnected before dispose |

Checkpoint verdicts: C1026-2 confirmed (the button and charts ignored a live system change; f69-02 fixed it). C1026-3, C1035-2, C1044-2 and C1375-1 confirmed: right to the end, the chart test watched a fresh page rather than a redraw, and the height test compared the two themes rather than the bar before the button. Each fix ticket closed part of the gap, never all of it. Missed by the checkpoints, visible in the diffs they read: F1 (f69-01, f69-02), F2, F4 and F5 (f69-01).

Score: 6/10. The feature does what the plan said, with no flash, a choice per device, charts that follow and a phone row that holds. The code the local model wrote was close. But it shipped with a leak into the night theme and a choice the system could undo, and five tickets and about 5.6 hours went into tests that still didn't prove the redraw.

Checked and fine: the inline script sits after the stylesheet rather than before it, as the ticket said. That's harmless: an inline script after a stylesheet runs before the body paints, so there's no flash. The light tokens still pass 4.5:1 on every plate. No new colours.

Tests: after the fixes, the 44 theme, top-bar and floor tests pass. The full `tests/runner tests/factory_dashboard` run took longer than this job's 10-minute background limit and was stopped at about 98% with nothing failed; two `E`s printed as it was killed. The last six files on their own (`test_app.py`, which this review edited, and `test_reports` to `test_timeline`) pass: 269 tests. Ruff is clean. The runner's gates run the whole suite before any merge. The rest of this diff range belongs to other milestones (F15, F51, F68, F81, F82, F114, F164 and others) and their own reviews.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Nothing new.

## Factory
- Flow: one feature ticket and five fix tickets, all by the local model. The first four checkpoints were Copilot standing in for Claude. f69-06 parked about 3.8 days for a Claude direction. No stops for you, no limits hit.
- Models: Qwen3.6 35B did all the building, about 8.2 hours of model (2.6 on the feature, 5.6 on fixes). It got the mechanism right but not the edges (scope, the stored choice, the tap target), and it couldn't write a test that watched a redraw. The stand-ins judged each newest test fairly, but never looked past the tests to the page. One Opus direction ($0.69) unparked f69-06.
- What to change: f68-08 (landed) covers the chain. The browser step for checkpoints is in 6, for you to plant if you want it. The CSS scope check is new in the tests.

<!-- runner report -->
<!-- /runner report -->
