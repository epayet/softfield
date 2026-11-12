# Review: F230, Queue rows squeezed into the number column

## Sign-off sheet

### 1. What changed
On the Overview's Queue panel, "Fast lane goes before everything" now sits on one line, on the phone too, instead of one word per line. The same goes for queued jobs (Planning, Plant, a direction): their text uses the whole row.

The fast lane looks like its bay again. Each of its rows, from the label down to the bay's end, has the yellow-and-black hazard stripe on its left, and the label is back in its uppercase display type.

The review also put back two things the change broke on the way:
- The big number in "**3** TICKETS WAITING." had lost its size.
- The stripe was drawn over the first letters of the label.

Card with no mock-up (D3: it restores F172's look), so there's nothing to compare.

### 2. How to test it yourself
1. With a card in the fast lane, open the Overview on the phone and scroll to Queue. "FAST LANE goes before everything" should be on one line, its text clear of the striped edge.
2. Below the bay, a queued Planning or Plant row should read across the whole row, not as a narrow column of words.
3. Ticket rows should still show their number in the narrow left column.
4. The count above "Next in line" should be the large number with small caps after it.
5. Do the same on a wide screen and in the light theme.

### 3. Left for later
Nothing set aside. One nit, not worth a run (see Findings).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-06 to 2026-11-09: the planner was parked twice because Claude was limited, then the card was planned.
- 2026-11-09: the local model's attempt 2 timed out, and the ticket was parked until Claude's reset gave direction.
- 2026-11-10: the local model (Qwen) merged it on attempt 3, with the lead's direction. Model time was 37 minutes, checks 9 minutes, and 5.2M tokens went in for a 15-line change.
- 2026-11-12: Claude reviewed it and fixed three should-fix findings itself (CSS and the test, about 20 lines).
- Lessons:
  - "Delete the unused rules" let the developer delete one rule too many (`.count`). A ticket that removes CSS should name the exact selectors to remove, and the gates have no check for a class the templates use but the stylesheet no longer defines.
  - The browser test checked the one row the owner reported and skipped the two other Done when lines (the Planning row, the 28px column). So nothing looked at where the text started, and the stripe over the label went unseen. The review rewrote the test and proved by hand that it fails: it took each fix out and saw the test go red.
- Logs: `.softfield/sessions/2026-11-09-1619.md`, `.softfield/sessions/2026-11-10-0229.md`, `.softfield/sessions/2026-11-10-1232.md`.

### 6. What next
- **Product:** product work is still on hold, as you asked.
- **Factory:** a gate that lists every `class="…"` in the dashboard's templates that no stylesheet rule matches would have caught F1 before the merge. It's worth a ticket if a missing style turns up a second time. For now it's a lesson, not a check: a check for one occurrence is ceremony.

### 7. What clogged the factory line
Most of the four days from planting to merge were waits for Claude's limits: the planner was parked twice (2026-11-06 and 11-07), and the ticket's direction was parked on 2026-11-09. The local model's time went on one timed-out attempt and a 37-minute successful one. To unclog: the reserve for planner jobs (ADR 20 item 2) is what would have let this one-line bug through sooner. Nothing new to add.

<!-- runner report -->
<!-- /runner report -->

## What was built
`f230-01-queue-rows-full-width` (local model, 3 attempts):
- `.belt li:not(:has(> .n))` spans both columns.
- A `lane-row` class marks the bay's middle rows, and `.lane-label`, `.lane-row` and `.bay-end` carry the hazard stripe in `::before`.
- The dead `.lane-bay` rules are gone.
- Two tests were added at the end of `test_overview.py`. The session report says it "edited existing tests", but the diff only adds lines, and no existing test changed.

## Findings and resolutions
- **F1 (should-fix, fixed by Claude):** `.count` and `.count small` were deleted along with `.lane-bay`, but `_partials/queue.html` still uses them, so the queue's count shrank to body text. Restored, and the browser test checks the 28px size.
- **F2 (should-fix, fixed by Claude):** `.belt li` has no left padding, so a row without a number started its text at the edge, and in the lane the 5px stripe covered it (a 3px gap, measured). Rows without a number now have 10px of padding, and the lane's 14px. The test checks the label clears the stripe.
- **F3 (should-fix, fixed by Claude):** the browser test checked only the lane label's height, not the Planning row or the 28px column that its Done when also names, so F2 went unseen. Rewritten, and checked to fail without the full-width rule and without the padding.
- **F4 (nit, report only):** `test_the_fast_lane_rows_carry_the_hazard_stripe` checks class names, not the stripe. The browser test covers what shows now.

Checkpoint: the 2026-11-10 checkpoint re-checked this ticket and raised nothing, so F1–F3 are marked missed. Score 5: the main bug is fixed, but two regressions and a test that couldn't fail went through.

No French in this milestone.

Checks after the fixes:
- `test_overview.py` and `test_app.py`: 371 passed.
- `test_line.py` and `test_board.py`: 289 passed.
- ruff: clean.
- The whole `tests/runner tests/factory_dashboard` run was stopped twice at the 10-minute call limit, with no failure up to 62%. The machine was slow (7.5 minutes for `test_overview.py` alone). The fixes only touch `dashboard.css` and one test, so the runner's tests can't see them. The runner's own gates run everything before this merges.

## Workflow observations
- About 5.2M local tokens for a 15-line CSS and template change, after a timed-out attempt. The difficulty-2 rating was right, but the model spent its time on the browser test.
- The developer tested the line the owner reported and skipped the other Done when lines, the pattern of F188 and F77. No new gate for it: a gate can't tell which Done when line a test covers. The review reading each line against the tests is what catches it.
