# Review: F106, where blocked tickets go for you to review

- **Status:** done, signed off by the owner on 2026-10-21.

## Sign-off sheet

### 1. What changed
When the runner gives up on a ticket, you now hear about it at once. Before, a blocked ticket sat in a folder until a milestone ended, with no button to bring it back.
- **Your desk has a "Blocked tickets" group,** second after "Didn't go through". Each item shows the ticket, why it was blocked and how many tickets wait behind it. The Overview's "Needs you" counts it through the desk, so it isn't counted twice.
- **Two buttons on each item: "Try again" and "Set aside".** A press shows the item as on its way at once (dashed orange). At its next pick the runner puts the ticket back in the queue or moves it to Set aside. Either way the failed work is kept on a branch, `blocked/<id>`.
- **The lead looks first.** When a card's ticket is blocked, the runner writes a message on that card's thread, shown as "The runner", and the lead answers with what went wrong and a fix to approve. The desk item says where that stands: "the lead is looking at it", then "the lead's fix waits on F…'s thread". If you approve the fix, the ticket comes back reworked or set aside, and its desk item clears. A bug ticket has no card, so it gets the buttons only.
- **A red main no longer blocks good work.** If a lead ticket fails a check that main fails too, it isn't blocked. Its work waits on its branch, you get one "Needs you" item naming the failing check and the ticket that would fix it, and the lead's other tickets wait until main passes again. Developer tickets keep going.

### 2. How to test it yourself
1. On a phone, open the dashboard's Planning page the next time a ticket is blocked (or ask in a terminal session for one to be blocked on purpose). Check that "Blocked tickets" shows the ticket with its reason, and that the Overview's "Needs you" counts it once.
2. Open that card's thread. You should see the runner's message, then the lead's reply with a fix to approve once its planner job has run.
3. Back on the desk, press "Try again" on a blocked ticket. The item should turn dashed orange at once, with no buttons. After the runner's next pick, the ticket should be under Tickets → ready and gone from the desk.
4. On another blocked ticket, press "Set aside". After the next pick it should be in the Tickets page's Set aside table.
5. While the lead's look runs, the blocked item should end with "the lead is looking at it"; once the lead has replied, with "the lead's fix waits on F…'s thread".

### 3. Left for later
Two backlog nits, nothing you need to act on:
- the Overview's queue shows a look's planner row with its reason only, not the runner's message;
- "the lead's fix waits" is said after any lead reply on that card's thread, not only the reply to the look, and the item links to the ticket rather than the thread.

### 4. Decisions waiting for you
None. ADR 29 was accepted on 2026-10-13, and everything here follows it.

### 5. How the work went
- 2026-10-15 22:31: f106-02 (the desk group), developer, merged on its third attempt (two stops, then a direction from the lead), 2.1M local tokens ([session](../sessions/2026-10-15-2231.md)).
- 2026-10-20 07:54: f106-01 (the item and the two requests), lead ticket, merged at the end of a long 16-hour session ([session](../sessions/2026-10-20-0754.md)).
- 2026-10-21 00:21: f106-03 (the buttons) and f106-06 (red main), lead tickets, both first time ([session](../sessions/2026-10-21-0021.md)).
- 2026-10-21 02:11: f106-04 (the lead's look), lead ticket, first time ([session](../sessions/2026-10-21-0211.md)).
- 2026-10-21 03:37: f106-05 (a replan brings a blocked ticket back), lead ticket, first time ([session](../sessions/2026-10-21-0337.md)).
- 2026-10-21 04:34: round 1 review, F1 fixed by the lead ([session](../sessions/2026-10-21-0434.md)).
- 2026-10-21 05:12: f106-07 (the item names the lead's fix), developer, first time, 1.2M local tokens ([session](../sessions/2026-10-21-0512.md)).
- Lessons:
  - Five of the six tickets were the lead's, since `runner/` is protected. All five passed on their first attempt, but each restarted the runner, because a change to `runner/` needs a fresh process. The four sessions on 2026-10-21 were one ticket or two each, for that reason.
  - The plan's "keep the failed work" rule (D3) was built for one of the three ways a ticket leaves `blocked/`. Each ticket was right on its own, and the gap showed only across 01 and 05. The review fixed it in all three places.
  - D4 was written as a decision but no ticket carried it. A decision with no ticket in the table is now something this review looks for.
  - A small, well-pointed fix ticket (one function, an example to follow, the four test cases named) went to the developer and passed first time, as ADR 17 item 5 intends.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Watch the first real block. It will be the first time the runner writes on a thread and the lead answers it without you. Check that the reply is a `replan` you can approve in one tap.
  - When the lead plans a card, check that every decision is named by at least one ticket in the table. f106-07 would not have been needed if D4 had had one. This belongs in `docs/task-writing.md`'s plan checklist; worth a line there next time it changes.

### 7. What clogged the factory line
- **Restarts after `runner/` changes:** each of the five lead tickets stopped the runner. That cost four sessions instead of one, and some idle time between them (2026-10-21 00:21 → 03:37). Protected work in a row will always do this; ordering the lead's runner tickets together, as here, keeps it to one restart per ticket.
- **f106-02's two stopped attempts** (≈73 min of model time, 22 min of gates) before the lead's direction. The local model stalled twice on a desk change. Its third try, with the direction, passed.
- **A long gap between the developer ticket and the lead's:** f106-02 merged on 2026-10-16 and f106-01 on 2026-10-20, with other cards' work and Claude's usage limits in between (several planner jobs and checkpoints parked in the 2026-10-20 session). Nothing to unclog in F106 itself.

The hours behind these are in the runner report below.

## What was built
- `runner/loop.py`: `block` stores a `blocked` owner item ("<id> blocked: <reason> · N tickets wait behind it") and queues the lead's look (`_look_at_block`, `_queue_look`). `move_to_ready` also takes from `blocked/`, `set_aside` is new, and both keep the failed work (`keep_blocked_work`, this review). The red-main check (`_main_is_red`, `_look_at_main`, `waits_for_main`) holds the lead's tickets while main fails what they failed, and a waiting ticket merges from its branch with no new session.
- `runner/checks.py`: `check_all(only=…)` runs just the named checks, used on main.
- `runner/requests.py`: the `set_aside` request; `queue` and `set_aside` resolve the desk item. A replan may bring its card's blocked tickets back to `ready/` or `later/` (`_why_not_blocked`, `_brought_back`, `_unblock`), and is refused for another card's, for one removed and put nowhere, or for one edited in place.
- `runner/planner.py`, `runner/metrics.py`: the runner as a thread author, the look's subject `<card>#m<message id>`, and its prompt line.
- `runner/owner.py`: the verdict writes the same item text, with no command.
- `factory_dashboard/planning.py`, `templates/planning.html`: the "Blocked tickets" group, its two buttons, and on-its-way. `templates/thread.html` draws the runner's message. `overview.py` counts blocked items through the desk only.
- Docs: `docs/workflow.md`, `docs/task-format.md`, `docs/agents/lead.md`.

## Findings and resolutions
- **F1, should-fix, fixed by the lead.** A lead ticket's failed work was copied to `blocked/<id>` only on Try again. A ticket set aside and later queued from `later/`, or brought back to `ready/` by an approved replan, started again from main and lost it, against D3. Now `keep_blocked_work` in `runner/loop.py` is called by all three: `move_to_ready`, `set_aside` and `requests._unblock`. Tests: the set-aside test asserts the copy, and the new `test_a_blocked_ticket_brought_back_keeps_its_failed_work` covers the replan path. `docs/workflow.md` says so.
- **F2, should-fix, fixed by f106-07 (developer, first attempt).** D4 and the first expected outcome want the blocked item to say what the lead suggests. No ticket built it, so the item showed the reason alone. Now `_blocked` adds "the lead is looking at it" from the runner's look message, or "the lead's fix waits on F<n>'s thread" once a lead message follows it on the same thread. Four new tests check the words exactly, including a look about another ticket on the same thread; the session report flagged `test_planning.py` as edited, but the diff only adds tests. Words only, so no mock-up.
- **F3, nit, backlog (round 2).** Any lead message after the look counts as the lead's fix, so a reply to another of your questions on that thread, before the look's job runs, would say the fix waits too. Rare, and the thread shows under "Your answers wanted" either way. The backlog item reads the look's own planner row instead, and links the item to the thread.
- **Checkpoint finding f110-…-C965-1 (nit), rejected.** The "resolved" and "no open blocked" tests read the page with `groups.get("blocked", "")`, which is weak, but each also asserts `desk()`'s blocked group directly. In the second test an absent group is the expected result. The checkpoint itself said "the `desk()` asserts carry them".
- Existing tests a developer edited: in f106-02, `test_other_kinds_still_show_with_their_command` now expects a blocked item outside "Needs you" (D1 asks for that) and gained a reserve item, so the test still checks something. In `test_planning.py`, the group count went from five to six. Both are right.
- Read and found sound: the red-main hold, which never holds the ticket that would mend main or developer tickets, and rechecks main only after a commit that touches code (an unknown old head counts as changed). The look's thread handling: an archived thread opens again, and a bug ticket gets no look. The replan's refusals, with a test for each.
- No French: nothing in `coucou/` changed.
- Round 2 checks: `test_planning.py`'s blocked tests (23) and `test_requests.py`'s blocked and set-aside tests (18) pass.
- Score: 8/10. A careful set of tickets with strong tests. Two plan-level gaps showed only across tickets; both are closed.

## Backlog
- Added: the Overview's queue shows a look's planner row without the runner's message (`queued_jobs` reads only `owner_requests`).
- Added (round 2, F3): "the lead's fix waits" should read the look's own planner row, and the item should then link to the thread.

## Workflow observations
- The review's full suite didn't finish again (F88's backlog item): `pytest tests/runner tests/factory_dashboard -x` and `softfield check-all` were both stopped at the 20-minute background limit, the first at about 75% with no failure. After the fix, what it touches was run in full and passes: `tests/runner/test_requests.py` and `test_owner.py` (318 tests), `test_loop.py`'s blocked, lead, main and queue tests (90), plus ruff and mypy on `runner/`. The runner's own gates run the whole suite at the commit.
- Lead tickets get no checkpoint, so F1 could only be caught here. It was a gap between two lead tickets, which no single checkpoint would have seen anyway.
- Expected outcome against actual: all three "Done when" items are met by the code. Of the expected outcome, only "with the lead's suggested fix" on the desk item is missing, and f106-07 adds it.

<!-- runner report -->
<!-- /runner report -->
