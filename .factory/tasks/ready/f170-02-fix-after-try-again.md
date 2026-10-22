---
id: f170-02-fix-after-try-again
milestone: f170-there-s-a-blocked-ticket-that
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
A replan that brings back a blocked ticket is still approvable after the owner pressed Try again on that ticket: its reworked ticket replaces the one Try again put back in `.factory/tasks/ready/`, instead of the approval being refused as a clash.

### Context
Read `.factory/cards/f170-there-s-a-blocked-ticket-that.md` ("What happened", D2), then `_approve_plan`, `_brought_back` and `_unblock` in `runner/requests.py`, and `carry_footers` in `runner/tasks.py`. Test-first.
- What happened on 2026-10-21: the lead's replan on F132 wrote f132-01-bar-follows-the-job's reworked ticket in ready/ on its plan branch at 15:59. At 21:23 the owner's Try again moved the blocked copy to ready/ on main (commit `4359d23`). The approval at 21:46 then hit an add/add conflict in `git merge --squash` and returned "plan/f132 clashes with main: not approved".
- The rule: for a replan, each of its card's tickets that the branch writes in `.factory/tasks/ready/` or `.factory/tasks/later/` while main holds the same file name in `.factory/tasks/ready/` and the ticket isn't the running one (`state.in_flight`): main's copy is the one Try again put back. Resolve it before the squash so the branch's version wins, carry main's runner footers onto it (`carry_footers`), as `_unblock` does for a blocked copy, and remove main's ready copy when the branch put the ticket in later/. Any other clash is refused as today.
- The approval's words name it: "f132-01-bar-follows-the-job: the lead's fix replaced the ticket Try again put back".
- Follow `test_approving_a_replan_brings_a_reworked_blocked_ticket_back_to_ready` in `tests/runner/test_requests.py`.

### Done when
- a replan brings back a blocked ticket, then a Try again on it is applied, then the approval: approved, the ready ticket is the branch's version with the blocked run's footers once (not twice), and the words say the fix replaced it
- the same with the ticket set aside in later/ by the replan: it is in later/ only, gone from ready/
- the ticket running at the approval: refused, as today
- a plan (not a replan) whose branch clashes with main: refused, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
