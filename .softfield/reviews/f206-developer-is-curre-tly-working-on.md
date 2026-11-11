# Review: F206, the board's developer's view counts tickets a developer has started

## Sign-off sheet

### 1. What changed
On the board's **Developers only** view, a card whose developer ticket is under way no longer says "lead only":
- while a developer works on a ticket, its card is lit and reads "developers: working on f187-02 · then the lead's f187-01";
- a developer ticket that waits on the running one counts as "after it", not as waiting for the lead;
- a developer ticket handed to the lead reads "developers tried f187-02 · now with the lead", a blocked one "f187-02 is blocked", and that card stays faded;
- the legend's faded entry reads "faded: nothing for developers to take";
- the Planted column's head counts a running ticket among what developers can work on.

No mock-up for this card, so nothing to compare.

### 2. How to test it yourself
1. On your phone, open the board and turn on **Developers only** while the runner has a developer on a ticket.
2. That ticket's card is lit and says "working on" with the ticket's name.
3. Find a card whose developer ticket was handed to the lead (the desk lists escalations): it's faded and reads "developers tried … · now with the lead".
4. A card with only lead tickets still reads "lead only".

### 3. Left for later
Nothing set aside.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-06 ([session](../sessions/2026-11-06-0111.md)): f206-01 merged by the local model in 2 attempts (first failed its own tests), 73 min of model time, about 6 M tokens in.
- 2026-11-11 review: the merged work got D1 and D2 right but lit the handed-on cards D3 says stay faded, and its tests asserted the wrong look under docstrings that said "faded". The lead fixed it directly (about 25 lines), since a fix ticket would have had a developer redo the same misreading.
- Lesson: a test's docstring and its assertion disagreed and every gate passed. Checking that a test asserts what its docstring says is a review habit, not something a gate can catch cheaply.

### 6. What next
- **Product:** nothing new from this card; the product stays on hold.
- **Factory:** the developer's view is now true while work runs. Next worth checking is the same view on a busy queue from the phone, which is how F206's gap was found in the first place.

## What was built
One ticket, f206-01 (`git show 6b9306f47`): `DevWork` gained `running`, `with_lead` and `blocked`; `_dev_resolver` follows a running developer ticket like a ready one; `_developer_totals` counts running tickets; `dev_tag` got the new lines and the legend its new wording.

## Findings and resolutions
| id | grade | what | route |
|---|---|---|---|
| F1 | blocking | Cards with only escalated or blocked developer tickets were lit (look `can`), against D3, and counted on the Planted head as a card developers can work on. The tests asserted `dev-can` under docstrings saying "is faded". | fixed by the lead |
| F2 | should-fix | On a lit card, an escalated or blocked developer ticket didn't count for "then", so a card with a running and an escalated ticket promised "then Claude's review". The test for that Done-when line had a lead ticket in it and so never hit the case. | fixed by the lead |
| F3 | should-fix | The handed-on words came first in `dev_tag`, so a lit card with work to take plus one escalated ticket read only "developers tried … · now with the lead". | fixed by the lead |
| F4 | nit | "f72-01, f72-02 is blocked". Now "are blocked". | fixed by the lead |
| F5 | nit | The developer edited `_three_looks` (F146's example) to make f70-01 running, so that test no longer checks the plain "N now · M after it" line. F233's test still checks "1 now · then Claude's review", so the coverage gap is small. | report only |

The fix in `factory_dashboard/board.py` (`_dev_work`): a card is lit by ready or running developer work, half-dark by waiting work, and otherwise faded, carrying its handed-on tickets for the words. "Then" counts escalated and blocked developer tickets as what's left. `board.html` puts the lit and waits lines first. Tests: escalated and blocked cards expect `dev-none`, and the head leaves them out. The "no lead ticket left" test now has no lead ticket. New tests cover two blocked tickets and a lit card with a blocked one.

A later card's test, F209's `test_in_the_developers_view_a_card_at_work_keeps_its_frame_at_full_strength`, depended on F1: its F71 had a running developer ticket and still expected the half-dark look. Under D1 that card is lit, so the test now gives F71 a running lead ticket with a developer job. That is the same arrangement it already used for F72, and the test still checks what F209 meant.

No French in this card. No checkpoint ran on f206-01, so there are no checkpoint findings to judge.

## Factory
- **Flow:** one developer ticket, merged on its second attempt. There were no stops or parks, and the owner didn't need to step in.
- **Local model:** it took 73 min and about 6 M input tokens on a difficulty-3 ticket. It made 12 edits in a row before running anything (session report). It wrote tests that pass against its own misreading. On every escalated and blocked test, the docstring said "faded" and the assertion said `dev-can`.
- **What to change:** nothing new as a gate. The lead caught it by reading the tests against the card's decisions. This is the "read the tests as closely as the code" rule doing its job.

<!-- runner report -->
<!-- /runner report -->
