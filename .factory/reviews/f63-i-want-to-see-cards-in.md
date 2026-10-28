# Review: F63, cards on the planning page in order of importance

- **Status:** round 1 done; one fix ticket open (f63-02-blocked-stays-second), then round 2.

## Sign-off sheet

### 1. What changed
- On the Planning page, **Coming** now comes first, right under the two tiles and as wide as the page, but only while something is on its way. What you just planted shows there, above the box you typed it in.
- **Plant an idea** comes next, then **Your desk**, then **Archived**, last as before.
- On the desk, **To sign off** (it was called "Finished, to talk through") comes before **Proposals to review**, then **Your answers wanted** (the conversations), then **Seeds**. **Didn't go through** stays at the very top when there is one, and **Blocked tickets** goes back to second once f63-02 is merged.
- Needs you on the Overview, and Previous and Next on a card's page, follow the same order.

### 2. How to test it yourself
1. On your phone, open Planning. With nothing on its way, the page starts with the tiles and then the Plant an idea box. There is no Coming.
2. Plant a short note. Within a second it shows under **Coming · 1**, above the box, and the box is empty.
3. On the desk, check that a card waiting for your sign-off is above the proposals, and the proposals are above the conversations.
4. Open the first conversation and press Next: it moves down the desk in that same order.
5. Open the Overview: Needs you lists the same items in the same order.

### 3. Left for later
- Nothing for this card once f63-02 is merged. F14 (Coming items you can tap) and F64 (the Plant box emptying) are separate cards that touch the same page.

### 4. Decisions waiting for you
- None. I decided myself where Blocked tickets go. The F63 card was written before F106 added that group, so it never said. I kept F106's place, second, because a blocked ticket stops the tickets behind it.

### 5. How the work went
- 2026-10-08: planned on Opus in about 2 minutes. Then it waited 20 days in the queue.
- 2026-10-28 ([session](../sessions/2026-10-28-1957.md)): f63-01 merged on its first attempt by the local developer. It took 58 minutes and 6.8M local tokens for a reorder of difficulty 2. A Sonnet checkpoint followed, then this Opus review.
- Lessons:
  - **A card that waits weeks goes stale.** The plan was written before F106 added a desk group, and the ticket listed only five groups. The developer guessed where the sixth went and got it wrong. Fix: f63-02. For the future, see Factory below.
  - **A browser test passed by waiting out the poll.** "Shows at once" passed in 5.7 s because the 5 s poll did the work the plant's own redraw no longer did. The test now allows 2 s at most.
  - **Tests that pick desk groups by position** had to change in four files for one reorder. f63-02 makes them pick by key.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - A ticket planned more than about a week before it is built should get a quick "still true?" re-read by the lead against the code it names. The re-read happens when the runner picks it, not when it is planned. Today's case was F106's group, which arrived in between. I suggest planting it as its own card (text below).
  - Browser tests that check "at once" should set a timeout shorter than the page's poll, so a poll can't hide a missing redraw.

  Ready to plant: *"Re-read stale tickets before they're built: a ticket planned more than a week ago gets a short lead check against the code it names when it is picked (F63's plan missed F106's desk group)."*

### 7. What clogged the factory line
- **The wait in the queue:** 20 days between the plan (2026-10-08) and the build (2026-10-28). The card simply sat lower on the board than other work. That is the board's order, not a clog, but it is what made the plan stale. Fix: the re-read suggested in 6.
- **The local developer's 58 minutes** for a reorder of difficulty 2. It made 17 edits in a row without running a command, and it re-sent about 82k tokens of context per step. That is cheap on your own GPU, so no change, but it is the developer's usual pace on template work.
- The hours behind these are in the runner report below.

## What was built
- `desk()` in `factory_dashboard/planning.py` returns its groups in the new order. "Finished, to talk through" is renamed "To sign off".
- `factory_dashboard/templates/planning.html`: Coming's poll wrapper sits above the Plant and desk row. It is always there now, and draws the section only when there are items, so a plant shows up even when Coming was empty on load.
- Tests updated for the new positions in `test_planning.py`, `test_proposal.py`, `test_thread.py` and `test_coming.py`.

## Findings and resolutions
| Id | Severity | What | Route | State |
|---|---|---|---|---|
| F1 | should-fix | After a plant, Coming waited for its 5 s poll. The plant script redraws only `#plant-row`, which no longer holds Coming, so this broke F13's "at once". | claude | fixed: the script also redraws Coming; the test now allows 2 s at most |
| F2 | should-fix | Blocked tickets moved from second to last, undoing F106 D1, which nobody asked for | local | ticket f63-02-blocked-stays-second |
| F3 | should-fix | No test of the page order (Coming, Plant, desk, Archived), although the ticket's Done when lists it | claude | fixed: `test_coming_then_plant_then_the_desk_then_archived` |
| F4 | nit | Coming sat flush against the tiles once it left the row | claude | fixed: 14 px top margin |
| F5 | nit | A test's name still says "five groups" | local | part of f63-02 |

Checkpoint finding C1534-2 ("planning.py's docstrings still say five groups") is **rejected**: `planning.py` says six in both places. Only a test name is stale (F5). The checkpoint missed F1, F2 and F3, all visible in the diff it read.

Tests the developer edited, read one by one:
- The index shifts are right for the order f63-01 built.
- `test_previous_and_next_step_through_what_waits` was rewritten for the new order and still checks "a page already done with leads to the first one left".
- The checks for `desk-coming` were narrowed to `<section id="desk-coming"`, because the poll wrapper now always carries that id. That is correct, but it hid the missing redraw (F1).

No French changes: the dashboard is English only.

## Backlog
- None.

## Workflow observations
- The checkpoint passed the work as sound and checked the order "by content". It didn't compare the new group order with the decision that placed the sixth group (F106 D1), and didn't notice that the JavaScript redraw targeted a block the change had emptied. A checkpoint on Sonnet reading a template move should follow every id the move touches to its uses in the page's script. I'm noting this here rather than adding a gate: it is one occurrence so far.

<!-- runner report -->
<!-- /runner report -->
