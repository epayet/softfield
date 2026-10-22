---
id: f153-02-sonnet-lead-checked-and-stepped-up
milestone: f153-i-wonder-if-sonnet-would-be
depends_on: [f153-01-lead-ticket-by-difficulty]
agent: lead
difficulty: 4
area: factory
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A lead ticket done by the first agent of `[roles] lead-ticket` (Sonnet), when the role lists two, gets one attempt by the second agent (Opus) on the same branch when its `check-all` fails, before it is blocked. A lead ticket done by the last agent listed runs exactly as today, and no lead ticket's merge is checkpointed.

### Context
Read Decisions D2 and D3 in `.factory/cards/f153-i-wonder-if-sonnet-would-be.md`, and `.factory/adr/32-sonnet-on-easier-lead-tickets.md` items 2 and 3. In `runner/loop.py`: `run_lead_task` and `_settle_lead_task` (as f153-01 left them), `block`, `_check_all`, `call_claude`, `note_merge` (don't change it: lead merges stay unchecked); `prompts.LEAD_TICKET` in `runner/prompts.py` (don't change it). In `tests/runner/test_loop.py`: `test_a_lead_ticket_that_fails_check_all_is_blocked_with_its_branch_kept` and `test_a_merged_lead_ticket_is_merged_by_claude`.
- The step-up job is a second `lead-ticket` job on the ticket (`rec.attempts = 2`), routed to the second agent with a reason line saying it steps up after the first failed `check-all`; its brief is `LEAD_TICKET` plus one line naming the branch's earlier work and the check-all output `_settle_lead_task` writes in the ticket's logs folder.
- Its session starts fresh: don't resume the first agent's session on another model.

### Done when
- the first agent's `check-all` failing starts one job on the second agent on `task/<id>` without resetting the branch; it passing merges the ticket with `merged_by` the second agent; it failing blocks the ticket with its branch kept, as today
- with one agent listed, or a ticket the last agent did, a failing `check-all` blocks at once, as today
- no lead ticket's merge, by either agent, adds to `state.unchecked`
- the listed `tests:` pass, and the new tests fail without the change
- all gates pass (see `docs/workflow.md`)
