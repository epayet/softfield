# Review: F74, one box per conversation on the planning desk

- **Status:** done, signed off by the owner on 2026-10-29.

## Sign-off sheet

### 1. What changed
When you reply on a thread, its box stays where it was, in "Your answers wanted", and turns dashed orange at once, saying when the lead's reply will come ("waiting for the lead · …"). It stays dashed after the runner picks your message up, and goes solid again only when the lead's reply is stored. No more duplicate box in Coming, and no more jumping between two places. The first message on a seed shows the same way: the seed leaves "Seeds, not asked about yet" and becomes a dashed box in "Your answers wanted". Coming is now called "Coming seeds" and holds only what you just planted. A dashed box never counts as waiting for you, so the Planning tab's number and Needs you don't change when you send a message.

### 2. How to test it yourself
1. On `/planning`, open a thread under "Your answers wanted" and send a reply.
2. Back on `/planning`: the same box, same group, now dashed orange with "waiting for the lead · …"; there's no Coming seeds section unless a plant is waiting. The Planning tab's number dropped by one.
3. Wait for the runner's next pick: the box is still there, still dashed (the one being written shows "Writing now" with its bar).
4. When the lead's reply arrives: the box is solid again, and the tab's number goes back up.
5. Write a first message on a seed: it leaves the seeds and shows as a dashed box in "Your answers wanted".
6. Plant an idea: it shows under "Coming seeds · 1", alone.

### 3. Left for later
Nothing from this card. F96 (most recent threads first in "Your answers wanted") is still a seed; the review kept today's order (by the lead's latest reply) so F96 starts from it.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-28 21:56 ([session](../sessions/2026-10-28-2156.md)): 1 ticket, `f74-01-one-box-per-conversation`, built by Claude Sonnet as a lead ticket, merged first time in 21 minutes for $0.94; 0 local tokens.
- Lessons: the move from Coming to "Your answers wanted" was faithful, and the ten Coming tests were turned into the same checks on the dashed box rather than deleted. Two things slipped: the solid boxes' order changed from "by the lead's latest reply" to "by when the thread began" (no test held the order), and Coming's thread markup was left in the template though Coming can no longer hold a thread. The review fixed both and added the order test.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** F96 (newest threads first) is a one-line change now that the order is tested: a good small next card. The dashed-box pattern (a request shows at once, where its result will land) is now used by proposals, archive, sign-off and messages; the rest of the desk could follow it the same way when a card asks.

### 7. What clogged the factory line
- Nothing: one 21-minute job, first attempt, no limit waits, no stops for you.

## What was built
- `factory_dashboard/coming.py`: `coming()` keeps only the plant rows, as "Coming seeds" (D1).
- `factory_dashboard/planning.py`: `_answers_wanted()` lists the lead's unanswered replies (solid), then the threads waiting for the lead's reply (dashed, `on_its_way`), whatever is stored, archived or not yet a thread, in the F84 order (being written, placed, the rest, those held for a limit) (D2, D3). `_asked()` reads the open `plan_message` requests a cancel hasn't struck; `_seeds()` leaves out a card with one on its way (D4). Counts unchanged, as dashed items were already out of `waiting_for_you` (D5).
- `factory_dashboard/templates/planning.html`: the Coming heading reads the group's name; the desk's dashed box carries F84's "Writing now" label and bar.

Tests: the Coming thread tests in `test_coming.py` became the same checks on the dashed box in "Your answers wanted", with their setups kept, plus a new check that Coming seeds holds only the plant; `test_planning._boxes` reads the dashed boxes from the desk; `test_proposal`'s F51 D4 test now expects the box to stay, dashed; `test_thread`'s cancel and runner-look tests follow. Each edited test was checked against D1–D5: the old expectations were exactly the behaviour removed, and none was weakened (several gained a check, e.g. the count before and after).

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | "Your answers wanted" re-sorted its solid boxes by when the thread began instead of the lead's latest reply | Fixed: `ORDER BY m.id` again; `test_answers_wanted_keeps_the_order_of_the_leads_replies` (`tests/factory_dashboard/test_proposal.py`), fails without the fix |
| F2 | nit | claude | Coming's thread-box markup (a linked item with the writing bar) left in the template, unreachable now that Coming holds only plants; `Place`'s docstring still said "Coming" | Fixed: the branch is gone, the docstring follows |

No checkpoint ran (the only ticket was a lead ticket), so there are no checkpoint verdicts. Score: 8/10: a faithful, well-tested move of one rule from one group to another; one unintended order change and some dead markup.

Checked and fine: an archive on its way still words a dashed box through `_acted_on`; a cancelled message waits for no reply (`_asked`); plant-and-ask stores its thread at the pick, so it moves from Coming seeds to a dashed box as the card says; the "Writing now" styles in `dashboard.css` are shared, so the desk box picks them up. Ruff passes; runner and dashboard tests pass.

The French: no `coucou/locale/fr/` change in this milestone. No browser here for screenshots; the layout tests cover the desk.

## Factory
- Flow: one lead ticket on Sonnet, first attempt, no stops for the owner, no limit waits, no parks.
- Models: Claude Sonnet built it ($0.94); the local model had nothing to do. The card planned it as a developer ticket ("D"), the ticket said `agent: lead`; on Sonnet at under a dollar that was the right call for a move across three files with ten tests to turn.
- What to change: when a ticket rewrites a query, the ticket should name what the old query's `ORDER BY` promised. Once is not a pattern yet; worth a line in `docs/task-writing.md` if it recurs.

<!-- runner report -->
<!-- /runner report -->
