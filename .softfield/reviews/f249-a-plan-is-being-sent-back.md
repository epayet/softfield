# Review: F249, a sent-back plan shows on its way

## Sign-off sheet

### 1. What changed
When you press **Send back** on a proposal, the card's box in "Your answers wanted" goes dashed orange straight away, says "being revised" and when the reply should come, and drops out of the desk's count. The proposal you sent back stays in the box as a dashed link until the lead's next reply replaces the set, both before and after the runner picks the send-back up. On the card's thread page, the comments you just sent show at once as your waiting message ("Sent", numbered points), and the reply box gives way to the wait, as it already does for a message.

No mock-up for this card (it reuses the existing dashed "on its way" look), so there is nothing to compare.

### 2. How to test it yourself
1. On your phone, open a card that has a proposal waiting for you and comment on one key point.
2. Press **Send back**.
3. Go to `/planning`. The card's box is dashed orange and says "being revised". The number on the desk is one lower. The proposal you sent back is still in the box, with a dashed link.
4. Open the card's thread. Your comments show under "Sent" as numbered points, and there is no reply box, just the wait.
5. After the runner's next pick, your message reads "I sent back your proposal …". The box is still dashed and the link is still there.
6. When the lead replies, the new proposals replace the dashed link, and the box goes solid and is counted again.

### 3. Left for later
Nothing deferred and no bug tickets. Two small notes (F3, F4) are kept in this report only.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-14: the plan was asked for at 10:19 and parked for Claude's limit (planner job 2242).
- 2026-11-16 19:19: the lead planned it, and you approved it at 19:27.
- 2026-11-16 21:01–22:26: f249-01 was merged by the local model (Qwen) on attempt 2. Attempt 1 stopped after 20 minutes with no edit. Local tokens: 6.47M in. Session: [`.softfield/sessions/2026-11-16-2059.md`](../sessions/2026-11-16-2059.md).
- 2026-11-17 03:07: this review. It had been parked at 22:26 because Claude's 5-hour window was 95% used.

Lessons:
- **The local model bent the code to fit an old test instead of updating the test.** One existing row said "a worked send-back removes the proposal", which contradicts D2. The developer kept the row and added a check that drops the proposal after the pick. As a result, half of D2 never shipped, and all gates were green. **What changed:** the lead fixed the code and the row in this review.
- **The new desk test listed the links but not whether they were dashed,** so the solid sent-back link passed. When "dashed" is part of Done when, a test has to check the class.

### 6. What next
- **Product:** product work is on hold (owner, 2026-10-04). Nothing to suggest.
- **Factory:** when a plan changes a rule an existing test encodes, the plan should name that test, so the ticket says to update it. Here, D2 replaced the rule in `test_a_proposal_the_owner_settled_is_not_among_the_proposals`, and the ticket didn't mention it. I'll do this in my own plans from now on; it doesn't need a ticket.

### 7. What clogged the factory line
- **Claude's limits:** about 57 hours. The plan was parked from 2026-11-14 10:33 to 2026-11-16 19:19 (job 2242, parked). The review then waited about 4.7 hours, from 22:26 to 03:07, for the 5-hour window. **What would unclog it:** planning F249 was a 1-minute Opus job. Planner jobs this small could run within the reserve that ADR 20 item 2 allows for planning.
- **A failed local attempt:** 20 minutes (attempt 1, no edit after 20 min). **What would unclog it:** nothing new. The no-edit stop did its job.
- **Waits on you:** 8 minutes between the plan and your approval.

<!-- runner report -->
<!-- /runner report -->

## What was built
- `factory_dashboard/planning.py`:
  - `_asked` counts an open `send_back` for the card before the `/` (D1).
  - `_listed` keeps a sent-back proposal as on its way (D2).
- `factory_dashboard/thread.py`: an open `send_back` shows as the owner's waiting message, with its comments as points, and the lead's reply shows as pending (D3).

## Findings and resolutions
| id | grade | route | what | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | After the pick, `_listed` dropped the sent-back proposal: it had its own copy of `WORKED` to check whether the runner had worked the request. A kept sent-back link was also drawn solid, because only the `ON_ITS_WAY` state is dashed. | Fixed: `SENT_BACK` now maps to `ON_ITS_WAY`, and the hand-copied check is gone. `_asked` is now one comprehension. |
| F2 | should-fix | claude | No test covered the case after the pick, and none checked that the link is dashed. The old test row for a worked send-back still expected the opposite of D2. | Fixed: the row now expects the proposal kept and dashed, with a pending send-back row beside it. The desk test checks the link classes. New test: `test_a_picked_up_send_back_keeps_its_proposal_dashed_until_the_lead_replies`. |
| F3 | nit | report | The thread's waiting message shows your raw words until the pick, then the stored "I sent back your proposal …" version. Both are correct; the words just change once. | Left as is. |
| F4 | nit | report | The thread's `send_back` query matches with `LIKE`, so `_` or `%` in a thread key would act as wildcards. Keys are only `fN` or `general`, so nothing matches wrongly today. | Left as is. |

There were no checkpoint findings to judge. Score: 6/10. D1 and D3 are right, but D2 was only half done, and the gates were green because a test contradicting D2 was worked around rather than updated.

`uv run pytest -q tests/runner tests/factory_dashboard`: 3579 passed. Ruff and mypy are clean on the touched files.

French: none touched (factory only).

## Set aside
Nothing.

## Stop reason
None. All findings are resolved or kept in this report, so the loop can end after this round.

## Factory
- **Flow:** the plan was parked about 57 hours for Claude's limit, and the review about 4.7 hours. You stepped in once: the approval, 8 minutes after the plan.
- **Models:**
  - Qwen 3.6 35B, local: merged on attempt 2 (73.8 min of model time, 10.6 min of gates). It edited two existing test files and added a check to the code that worked around a test it should have updated.
  - Opus: planned in about 1.5 min; this review fixed F1 and F2 directly, about 15 lines of code plus tests. The lead did this rather than a developer because a developer had already missed the same point once.
- **What to change:** when a plan's decision contradicts a test that already exists, the lead's plan names that test, so the ticket tells the developer to update it.
