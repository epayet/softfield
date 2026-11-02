# Review: F15, reorder the cards from the board

- **Status:** done, signed off by the owner on 2026-11-02.

## Sign-off sheet

### 1. What changed
- **You reorder on the board now.** Each card shows its place in its stage (#1, #2…) instead of a P number. Drag a card by its grip (⠿), or use its ⋯ menu (Top, Up, Down, Bottom). A moved card gets a dashed orange edge and says "moved · was #7 · not sent yet". Put it back where it was and the mark goes. A bar at the bottom counts the moves, with Cancel and Send new order.
- **One send, then on its way.** Send new order sends the whole order once. Until the runner's next pick, the moved cards say "on its way · was #N · at the runner's next pick", on any device. Then the runner sets the cards' priorities in one commit, changing as few files as it can, and Next in line follows.
- **The board opens on the field.** Plots in growth order, each with its plant and its count. On a phone, tap a plot to see that stage alone. Nothing scrolls sideways.
- **A card says what it waits for.** A planted card whose tickets can't start yet says "waits for F9" (or the bug's name). You can see this on the board today: F61 and F77 wait for F9, and F62 and F97 wait for F132.
- **The ⋯ menu also has the card's actions:** Open its conversation, Set aside (seeds and sprouting cards; it says "on its way" until the runner does it) and Open the card.
- **The ↑ ↓ arrows are gone** from Next in line and the Milestones page. Next in line links to the board instead. The Queue panel's terminal command went with them.

### 2. How to test it yourself
1. On your phone, open the board and tap the Planted plot. Drag a card by its grip to the top. It should read "moved · was #N · not sent yet", and the bar should say "1 card moved".
2. Drag it back to where it was. The mark and the bar should go.
3. Move two cards, then press Send new order. Both should read "on its way … at the runner's next pick", and nothing else should be marked.
4. After the runner's next pick, the marks go and the order stays. Open the Overview: Next in line follows the new order and has no arrows.
5. Open the Milestones page: no arrows there either.
6. On the Sprouting plot, press ⋯ on a card. You should see the moves, then Open its conversation, Set aside and Open the card. Only press Set aside on a card you really want to set aside.

### 3. Left for later
- f15-11 (ticket, tests only): a test that a send the dashboard refuses keeps your moves and lets you press again. The code already does this; nothing tests it yet.
- One nit in `docs/backlog.md`: from bug-100 on, the board and the runner would break ties between two bugs differently. Nothing to do until the bug numbers reach 100.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-14 ([session](../sessions/2026-10-14-0427.md)): f15-01, the `reorder` request in the runner (lead, protected). Merged first time in 25 minutes.
- 2026-10-19 ([session](../sessions/2026-10-19-2316.md)): f15-02, the order on the board. Merged first time. It had waited 5 days for F110's f110-03.
- 2026-10-20 00:08 ([session](../sessions/2026-10-20-0008.md)): f15-03 the field, f15-04 drag and send, f15-05 the replan and f15-07 the arrows (all lead, all first time), then f15-08 "waits for" (Qwen, second attempt after a 75-minute timeout).
- 2026-10-20 07:54 ([session](../sessions/2026-10-20-0754.md)): f15-09 and f15-10, the two fixes from the checkpoint. Qwen took 3 attempts and a direction for the first, and 1 attempt for the second.
- 2026-10-29 22:21 ([session](../sessions/2026-10-29-2221.md)): f15-06, the ⋯ actions. It had waited 9 days for f73-02. Qwen stopped three times with no edit, and the lead finished it in 15 minutes.
- **Lessons:**
  - Sending the new module, the script and the phone layout to the lead was right: 6 of 6 passed first time, for $11.36.
  - The one small ticket Qwen passed (f15-08) had a field filled where it shouldn't be and tests that only checked the words were there. Fixing those took two tickets and 4 hours of model for 4 lines of code. Lesson added to `docs/agents/lead.md` (Known range).
  - A slow model night is still handled by hand. This was the fifth time in two nights, so it is now a ticket (bug-48), not another line in `lead.md`.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - bug-48 should run before the next night run. It stops a slow night from costing a direction and a third 20-minute attempt on every ticket.
  - With the board now holding the order, the Seed column holds 43 set-aside bugs above the cards. F174 ("Which bugs are set aside in the Seed column, and which to queue") is already a seed for that. I'd plan it soon, so the Seed stage shows ideas again.
  - I'd also let a checkpoint fix a finding of under 5 lines itself, rather than write a ticket. f15-09 was a 4-line fix that took Qwen 2.7 hours.

### 7. What clogged the factory line
- **Failed local attempts, about 4.2 hours:**
  - f15-08's first attempt timed out after 75 minutes.
  - f15-09's first attempt timed out after 96 minutes, with the code right. The full test suite now takes longer than the gate's 20 minutes (F71 is about these timeouts).
  - f15-09's second attempt and all three of f15-06's stopped on "no edit after 20 min".
  - **To unclog:** bug-48 for the no-edit nights, and F71 or bug-06 for a suite that fits its gate.
- **Waiting on other cards, 14 days end to end:** f15-02 waited 5 days for f110-03, and f15-06 waited 9 days for f73-02. In both, the runner did other cards' work meanwhile, so nothing sat idle. It only made F15 long, not the line slow.
- **Waiting for Claude:** f15-06's direction was parked 43 minutes for Claude's reset, and f15-09's waited 13 minutes. **To unclog:** bug-48 removes the f15-06 kind of direction altogether.
- No stops for you, and no review rounds beyond this one.

## What was built
- `runner/requests.py` (f15-01): the `reorder` request. Its value is the board's whole open order. `_board` finds what can be placed (open cards, and bug tickets in ready/ or later/ that aren't running). `_numbers` keeps as many priorities as it can, using the runner's own tie order. `_commit_files` writes the changed card headers and bug `priority:` lines in one runner commit. A later open order replaces an earlier one ("replaced by a later order"), and keys it doesn't know are skipped and named.
- `factory_dashboard/board.py` (f15-02, f15-04, f15-08, f15-06):
  - each card's place in its stage;
  - the open order shown with "was #N", where what is out of place comes from the longest run the two orders share, not from what was touched;
  - `Board.line` for a send;
  - `Card.waits`, and `Card.thread` with `setting_aside` for the ⋯ actions.
- `factory_dashboard/static/board.js` (f15-03, f15-04, f15-06): one stage at a time under 900 px, then drag by the grip with edge scrolling, the ⋯ moves, the bar, one send, and the card's actions copied from its slot's `<template>`.
- `stage_icon.html` `plant()`: our own SVG plants per stage. `dashboard.css`: the plots, the grip, the sheet and the bar, with the hazard dashed edge.
- f15-07 removed `_partials/move.html`, `queries.moves`, the arrows' fields and CSS, and the Queue panel's terminal command.

## Findings and resolutions
- **F1 (should-fix, fixed by the review):** a card waiting on a bug ticket read "waits for BUGS". The bug's milestone is the standing `bugs` key, which no card on the board carries. It now names the bug's id, and `test_a_card_waiting_on_a_bug_names_the_bug` covers it (`factory_dashboard/board.py:303`).
- **F2 (should-fix, ticket f15-11, tests only):** the two "refused by the dashboard" branches in `board.js` are untested: your moves are kept and Send can be pressed again, and Set aside says "not sent, try again". The code is right; a test with `page.route` returning 500 pins it.
- **F3 (should-fix, factory, lead bug ticket bug-48):** five tickets in two nights got a direction and a third no-edit attempt for nothing. The check `lead.md` has asked for since 2026-10-29 is now a ticket: when a run already has two other tickets that ended on no-edit stops, a ticket with two of its own escalates at once.
- **F4 (nit, fixed):** f15-08 left a `ticket_to_milestone` dict that nothing read. Removed.
- **F5 (nit, fixed):** f15-10's `_card_note` test helper could read the next card's note when its own card had none. It now reads inside the card's own markup. The two no-op `_, _, _ = _card(...)` lines went too.
- **F6 (nit, backlog):** see "Left for later".
- **Checkpoint findings:**
  - C1080-1 is confirmed: `waits` was filled for every stage, though nothing showed it outside planted.
  - C1080-2 is confirmed: `in` let "waits for F22, F63" pass as "waits for F22".
  - C1091-1 is confirmed and fixed by the review: f15-09's test asserted an empty `waits` on seed, ripe and harvested cards that had no dependencies. Those asserts are gone, and the docstring now says what the test really checks (the sprouting F22).
  - C1106-3 is confirmed and fixed (above).
  - Missed by the checkpoints: F1 and F4, both in f15-08's diff, and F5, in f15-10's diff.
- **The edited tests:**
  - f15-10 changed about twenty `_card(...)` calls to unpack three values, all mechanical. Later tickets now use the third value.
  - f15-07 replaced the arrow tests in `test_milestones.py` and `test_overview.py` with tests that the arrows are gone. Nothing was weakened.
  - f15-06 changed the ⋯ label test and widened the "only a reorder is posted" test to allow `archive`, as its ticket said.
- **French:** nothing in `coucou/` changed.
- **Live board:** I read `/board` as text on real data. The places, the plots' counts and four "waits for" notes (F61 and F77 wait for F9, F62 and F97 for F132) all show.
- **Score:** 8/10. The feature does what the card asked, the protected part is careful (fewest files changed, one commit, a later order replaces an earlier one), and the browser tests drive it as you would on a phone. The developer part needed two fix tickets and still had an edge (F1).
- **Tests run in round 1:** `test_board.py` with `tests/runner/test_requests.py` (409 passed), and `test_milestones.py` with `test_planning.py` (153 passed). Ruff, format and mypy are clean on the changed files. I didn't run the whole `tests/runner tests/factory_dashboard` suite: it takes longer than one command may run here (the F88 backlog item). The files the review touched are covered by the runs above.

## Backlog
- Added: F6, tie order of bug ids from 100 on.

## Workflow observations
- The replan (f15-05) earned its place. It caught that f15-04 had built one shared sheet, not a menu per card, and rewrote f15-06 to match. It also caught the Queue panel's terminal command, against your 2026-10-13 rule.
- The stand-in checkpoint (copilot-auto) found two real weak points in f15-08. But each fix went to Qwen as a ticket, and a 4-line fix took 2.7 hours. Suggested above: a checkpoint fixes a finding of under 5 lines itself.
- f15-09's first attempt had the code right and still timed out on the full suite. The slow suite now costs developer attempts, not only reviews (F71, bug-06).

<!-- runner report -->
<!-- /runner report -->
