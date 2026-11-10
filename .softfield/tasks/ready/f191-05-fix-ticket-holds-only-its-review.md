---
id: f191-05-fix-ticket-holds-only-its-review
milestone: f191-why-is-the-lead-reviewing-something
agent: lead
difficulty: 6
depends_on: [f191-04-limit-in-a-round-parks-the-review]
files:
  - runner/loop.py
  - runner/milestone.py
  - tests/runner/test_milestone.py
  - tests/runner/test_loop.py
tests:
  - tests/runner/test_milestone.py
  - tests/runner/test_loop.py
---

### Goal
Under `softfield run`, a review hands its round's fix tickets to the main queue instead of running them itself, so the owner's requests, the planner's replies and the other projects never wait for a review's fixes, and nothing sleeps after a round.

### Context
Read cause 6 and D7 in `.softfield/cards/f191-why-is-the-lead-reviewing-something.md` (D7 replaces D5).
- `runner/milestone.py`: in `review_milestone`, after a round, `work_queue(s, milestone=milestone)` runs the card's fixes, then a stop `reason` ends the loop, then `_fix_held_by_the_week`'s exit (F219 D3: row finished, PARKED, no stop recorded). With `park`, drop the inner queue and take that exit whenever the card has tickets left in `ready/`. Without `park` (`runner milestone`), keep today's loop. `due_reviews` and `_reviewed` say why no stop may be recorded.
- `runner/loop.py`: `choose_ticket` (the lane's tickets first: the card's tickets go right after them), `_drop_covered_merges` (ADR 38: which merges skip the checkpoint), `dry_run_plan` (it calls `choose_ticket` too). `under_review(state)` is new, as D7 names it.
- Tests to follow: `test_a_review_waits_for_a_lead_fix_the_week_holds` and `test_a_review_parked_between_rounds_resumes_at_its_round_on_its_own_fixes` in `tests/runner/test_milestone.py`; `_turns` and the `project_round` tests in `tests/runner/test_loop.py` for the round.
- On 2026-11-10 F9's review kept the owner's requests waiting from 15:28 to 17:30, and coaster-ranker's from 14:31 past 17:45, while it ran f9-35 and f9-36 itself.

### Done when
- Under `softfield run`, a round (not the last) that files a fix ticket returns PARKED with its row done and no stop in `state.review_stop`. A planner job queued meanwhile, and another project's queued job, run before the fix.
- With two projects, the reviewed one second in the owner's order: after the round, the first project's requests are applied and its planner job runs before the reviewed project's own planner job (`project_round`'s order, not the review's).
- The fix then runs before every other ticket but the fast lane's and the parked ones whose reset has passed, the dry run naming it next too. The week's pace line and Claude's limits hold it as they hold any ticket.
- Its merge doesn't count toward a checkpoint.
- Once the card's tickets are done, the review comes due again and goes on from the next round, reading the fix.
- A last round (a stop `reason`) records its stop and returns, and its fixes run in the main queue in the board's order and count toward a checkpoint, as ADR 38 has it.
- After a round nothing sleeps, whatever is parked or limited.
- `runner milestone` runs its review's fixes inside the review, as today.
