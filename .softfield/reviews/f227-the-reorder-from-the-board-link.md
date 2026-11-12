# Review: F227, the Queue panel loses its "Reorder on the board" link

## Sign-off sheet

### 1. What changed
On the Overview, the Queue panel no longer ends with "Reorder on the board ›". The Board tab at the top still goes to the same page, for the same project.
- With nothing waiting, the panel now says only "The queue is empty.". There's no "Next in line" heading over an empty list.
- With only a review due, its row still shows under "Next in line", with no count above it.
- The count still says how many tickets are waiting. The developer's version had swapped it to the jobs' count ("1 job waiting." with 143 tickets in the queue). I fixed that in this review.

Differs from the mock-up in one way: the after pictures show "1 job waiting." where the mock-up (and the before picture) say "N tickets waiting.". Fixed in this review (F1). The list and the missing link match the mock-up.

### 2. How to test it yourself
1. On the phone, open the Overview with tickets waiting. The Queue panel should say "N tickets waiting." even when a review or planning job sits at the top of the list. The list should end with its last row, with no "Reorder on the board" link.
2. Tap the Board tab. It should open the board for the same project.
3. On a project with nothing waiting, the panel should say only "The queue is empty.".

### 3. Left for later
Nothing set aside. One small naming note, not worth a run (see Findings).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-05: Claude (Opus) planned the card and drew the mock-up in 2 minutes ($0.82).
- 2026-11-06: the local model (Qwen) did the one ticket on its first attempt in 35 minutes. Nothing was escalated.
- 2026-11-12: Claude reviewed it, fixed the count it had swapped and added two tests.
- Lessons:
  - The developer changed more than the ticket asked. It restructured the count while moving the list inside the `if`, and nobody noticed. The tests it edited covered only what it removed. The after picture showed the mistake at once ("1 job waiting." beside a queue of 143). Comparing the before and after pictures line by line is what caught it.
  - The ticket's Done when named the "only a due review" case, but nothing tested it. Now there's a test.
- Logs: `.softfield/sessions/2026-11-06-0111.md`.

### 6. What next
- **Product:** product work is still on hold, as you asked.
- **Factory:** the checks passed while the panel's main number was wrong, because no test held the count when tickets and a job wait together. A UI ticket that rewraps a block should say "keep everything else in it as it is", and the review should keep comparing before and after pictures, not only after against the mock-up. That is how this was caught, so nothing new is needed yet.

### 7. What clogged the factory line
Taken from the `jobs` table:
- **Waiting for its turn: about 1¼ days** from plan (11-05 11:26) to the developer (11-06 17:57), then **about 5½ days** for this review (11-06 18:33 to 11-12 03:45). Both waits were queue order, with other work going first. No agent sat idle because of it.
- No failed attempts, no limits hit and no stops for you.

<!-- runner report -->
<!-- /runner report -->

## What was built
`f227-01-no-board-link-in-queue` (commit b66c4b171):
- **Template:** `factory_dashboard/templates/_partials/queue.html` moves "Next in line" and its list inside the panel's "something waits" branch and drops the board link. That branch now also opens for a lane, a queued job or a due review alone, as the ticket asked.
- **Tests:** in `tests/factory_dashboard/test_overview.py`, the three link assertions are removed. The parked-review row now ends without the link. The `<li>` count floor goes from 3 to 2, which is fine: the link was one of the three. The empty-queue test now expects no "Next in line". All of these edits were what the ticket asked for.

There's no French in this milestone.

## Findings
| Id | Grade | Route | What |
|---|---|---|---|
| F1 | blocking | claude, fixed | The developer swapped the count's branches. With tickets waiting and a job queued, the panel said "1 job waiting.", and with only a review it said "0 tickets waiting.". Now the tickets' count comes first, the jobs' count only when no ticket waits, and there's no count with only a review. |
| F2 | should-fix | claude, fixed | Nothing tested the case Done when named (only a due review) or the mixed case that would have caught F1. Added `test_tickets_and_a_queued_job_count_the_tickets` (on `/` and `/live`) and `test_only_a_due_review_shows_its_row_and_no_count`. |
| F3 | nit | report | `test_next_in_line_shows_each_priority_and_sends_reordering_to_the_board` keeps its old name. It still checks there's no reorder control in the list, so the name still roughly fits. |

**No checkpoint findings.** No checkpoint ran on this milestone.

## Factory
- **Flow:** one ticket, passed on its first attempt, no stops, no limits, no parks. The local model took 27 minutes of model time and 8 minutes of gates for a 1-difficulty template edit, with about 1.5M tokens in.
- **Models:** the Opus plan cost $0.82. The local model's output had a real regression that the gates passed. Claude's review caught it from the pictures and fixed it.
- **To change:** nothing yet. If an unrequested change slips past green gates on another card, add a line to the developer's instructions: "change only what the ticket names inside a block you move".
