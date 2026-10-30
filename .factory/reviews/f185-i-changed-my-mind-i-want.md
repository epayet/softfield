# Review: F185, your answers before proposals on the desk, newest answer first

- **Status:** round 1 done (2026-10-30), no findings, waiting for your sign-off.

## Sign-off sheet

### 1. What changed
- **Your answers come before proposals.** On `/planning` the desk now reads: Didn't go through, Blocked tickets, To sign off, **Your answers wanted**, **Proposals to review**, Seeds. Didn't go through and Blocked tickets stay above the sign-offs, but they only show when something went wrong.
- **Newest answer first.** In Your answers wanted, the thread the lead replied to most recently is at the top. The dashed threads the lead still owes a reply stay after them, in the same order as before.
- **Everything that reads the desk follows:** Needs you on the Overview, the Planning tab's count, and Previous and Next on a thread page now go sign-off, then conversation, then proposal.

### 2. How to test it yourself
1. On your phone, open the Planning room. Under To sign off, the next group should be Your answers wanted, then Proposals to review.
2. In Your answers wanted, the top box should say the smallest "the lead replied … ago".
3. Open the first item on the desk and press Next until the end. You should reach the sign-offs first, then the conversations, then the proposals.
4. Open the Overview: Needs you lists them in that order too.

### 3. Left for later
Nothing from this card. Already queued and not part of it: bug-48, so a slow model night escalates without writing a direction first.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-29 22:21 ([session](../sessions/2026-10-29-2221.md)): f185-01 (developer, difficulty 2). Qwen stopped three times on "no edit after 20 min", the third under a direction. The lead did it on main in 18 minutes ($1.23, plus $0.59 for the direction).
- 2026-10-30 04:24 ([session](../sessions/2026-10-30-0424.md)): the review was parked once for Claude's 5-hour window (79% used, cap 75%), then ran in the next session.
- **Lessons:**
  - The ticket named the group-order tests and missed three others that pinned the old order: the order inside Your answers wanted (`test_proposal.py`), Previous and Next, and Needs you. A developer with the right code would still have failed. Now a line in `docs/task-writing.md`: a ticket that reverses an order greps every assertion of the old one.
  - A slow model night again: the sixth ticket in three nights with no edit after 20 minutes, and a direction was still written. bug-48 is the fix and is ready.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Run bug-48 before the next night run. On f185-01 it would have saved the direction ($0.59), a 40-minute wait for Claude's reset and a third 20-minute attempt.
  - F96 (the same "newest first" for the other groups) is still a seed. Now that you can see answers newest first, tell me if you want it for proposals and sign-offs too, and I'll plan it.

### 7. What clogged the factory line
From the jobs table for f185-01:
- **Failed local attempts, 60 minutes:** three Qwen attempts, each stopped after 20 minutes with no edit. **To unclog:** bug-48 (escalate after two no-edit stops in a run).
- **Waiting for Claude, 40 minutes:** the direction was parked from 23:06 to 23:46 for Claude's reset. **To unclog:** bug-48 skips that direction altogether.
- **The review waited** for the 5-hour window (parked at 04:24 at 79%). Nothing to change: the cap did its job.
- No stops for you, and one review round.

## What was built
- `factory_dashboard/planning.py`: `desk()` puts the `answers` group before `proposals` (D1; keys, names, colours and items unchanged). `_answers_wanted` lists the settled replies with `reversed(last)`, so newest first (D3), and leaves the on-its-way items (`placed + rest + later`, F84 D4) after them. `_last_messages` stays oldest first for its other callers. Both docstrings say so.
- Tests: the group lists in `test_planning.py` and `test_coming.py`; `test_previous_and_next_step_through_what_waits` now steps sign-off → general → proposal; `test_three_desk_items_show_their_count_links_and_tab` expects f9, f8, f7; `test_answers_wanted_keeps_the_order_of_the_leads_replies` became `test_answers_wanted_lists_the_leads_newest_reply_first` and also checks that a thread the lead still owes a reply comes after every answered one.
- `docs/task-writing.md`: the lesson above.

## Findings and resolutions
None. I read the code and every edited test:
- The code matches D1–D3 exactly, and nothing else reads the desk's order (searched the dashboard's code and templates).
- Every edited test still asserts as much as before. The renamed one asserts more (the waiting thread after the answered ones), and none lost a check. The card's three Done when are each covered: the group order, newest first, and Next from the sign-off to the conversation to the proposal.
- No French: the factory has no translations, and no words changed.
- No checkpoint ran on this card (one ticket, done by the lead), so there is nothing to judge there.

Score 8: correct and minimal, but the ticket missed three tests, so a developer couldn't have passed it.

## Backlog
Nothing new.

## Factory
- **Flow:** one ticket, escalated after three no-edit stops, done by the lead. No stops for the owner, no limits hit except the review's one park for the 5-hour window.
- **Models:** Qwen made no edit (5, 7 and 4 tool calls). Opus: direction $0.59, escalation $1.23, and this review.
- **What to change:** bug-48 (already ready). The ticket lesson is already written in `docs/task-writing.md`. No new rule.

<!-- runner report -->
<!-- /runner report -->
