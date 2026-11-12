# Review: F233, the board's developer's view counts tickets that wait for the lead's direction

- **Status:** done, signed off by the owner on 2026-11-12.

## Sign-off sheet

### 1. What changed
On the board's developer's view, a developer ticket that failed twice and waits for the lead's direction no longer counts as work developers can take now. Its card is half-dark and reads "developers tried f86-01 · waits for the lead's direction". It also no longer counts in the "Developers can work on N cards, M tickets" line above Planted. A developer ticket that depends on it waits too, and its card names the ticket it waits for.

So on a day like 9 Nov, when every developer ticket waited for Claude, the board says so, instead of "7 cards, 10 tickets".

Card with no mock-up (D2: the look and the tag already existed), so there's nothing to compare.

### 2. How to test it yourself
1. Wait until a developer ticket fails twice. The Overview's queue shows a "direction" job for it.
2. Open the Board, switch on the developer's view, and find that ticket's card. It should be half-dark and read "developers tried <ticket> · waits for the lead's direction".
3. The "Developers can work on …" line above Planted should not count that ticket.
4. Once the lead has given the direction (the direction job is gone from the queue), the card should light up again with "developers: 1 now".
5. Check on the phone too.

No direction is open right now, so step 2 can't be seen until one is.

### 3. Left for later
Nothing set aside. Two nits are not worth a run (see Findings).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-06: planted at 19:26. The planner was parked until Claude's week reset at 16:00 on 9 Nov (about 69 hours).
- 2026-11-09: planned at 16:15 as one developer ticket. The local model (Qwen) merged it at 17:16 on attempt 1, after 35 minutes of model time and 7 minutes of checks, with 3.4M tokens in.
- 2026-11-12: Claude reviewed it and fixed one nit itself, a 4-line cleanup.
- Lessons:
  - A small, well-specified ticket that points at an example to copy (F206's escalated case and its test) passes first time on the local model. The ticket named every Done when line, and the four tests cover each of them.
  - The card's own question ("why is the factory not doing anything?") was answered from the metrics database before planning: the line was right to wait, and only the board was wrong. Reading the data first kept the fix to one dashboard ticket, with no change to the runner.
- Logs: `.softfield/sessions/2026-11-09-1619.md`.

### 6. What next
- **Product:** product work is still on hold, as you asked.
- **Factory:** the real cause behind this card was Claude's week running out on 5 Nov, mostly on planner replies ($223 of $308). F177 (planner replies record their real cost and start cold threads fresh) is the fix that matters, and it is already planted, #19 in Planted. I'd move it up.

### 7. What clogged the factory line
- **Claude's week:** the planner waited about 69 hours, from 6 Nov 19:26 to the reset on 9 Nov 16:00. F177 above would unclog it.
- **Merge to review:** the ticket merged on 9 Nov at 17:16, but the review was queued only on 12 Nov at 05:27. During that time other cards' directions and checkpoints were waiting on Claude's 5-hour window (the session log shows it at 80–92%, over its 75% cap). Nothing new to add: the same limits caused it.
- The local model's own time was 42 minutes, and nothing failed.

<!-- runner report -->
<!-- /runner report -->

## What was built
`f233-01-direction-is-the-leads` (local model, 1 attempt):
- `board()` reads once the open `work_queue` rows of kind `direction` for the project.
- `_dev_work` counts a ready developer ticket with an open direction as waiting, records it in a new `DevWork.waits_direction`, and keeps it out of `now` and `after`.
- `_dev_resolver` treats a dependency with an open direction as lead-side, so a ticket that depends on it waits and names it.
- The `dev_tag` macro has a new branch: "developers tried … · waits for the lead's direction".
- Four new tests in `test_board.py` cover the Done when lines: a direction-only card, a dependant, a mixed card that stays lit, and a finished direction. The session report says the ticket "edited existing tests", but the diff only adds lines, and no existing test changed.

## Findings and resolutions
- **F1 (nit, fixed by Claude):** `_dev_work` gained a `by_name` parameter, and the caller passed the same dict for it and for `rows`, so one dict had two names. Removed it.
- **F2 (nit, report only):** a card with one ticket waiting for its direction and another waiting for a lead ticket reads only the direction wording. Both waits are the lead's, and the card's look is right.
- **F3 (nit, report only):** the first test checks the "Developers can work on" count by summing the lit cards, not by reading `Board.developers` itself. That is equivalent today.

Checkpoint: the 9 Nov checkpoint (Copilot standing in for Claude) raised nothing on this ticket. That is fair, since only nits came up. Score 8: correct, well tested, first-time pass. It lost points only for the duplicated parameter.

No French in this milestone.

Checks after the fix:
- `test_board.py`: 149 passed.
- ruff and mypy on `board.py`: clean.
- The full `tests/runner tests/factory_dashboard` run was stopped by its time limit at 79% with no failures. The errors printed after the stop come from the stop itself. The fix only touches `_dev_work`'s signature in `board.py`, which only `board.py` calls, and the runner's gates run everything before the merge.

## Workflow observations
- The ticket used 3.4M local tokens for a ~50-line change. That is in the usual range for a difficulty-2 dashboard ticket. The session flagged 9 edits in a row without running a command, but the result was clean.
- The planner's "What happened" section is a good pattern for question-cards: it answers the owner's question with dated numbers and separates "the line was right" from "the board was wrong".
