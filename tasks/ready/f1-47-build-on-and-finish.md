---
id: f1-47-build-on-and-finish
milestone: f1
depends_on: [f1-46-parking-and-reserve]
agent: lead
difficulty: 6
files:
  - runner/loop.py
  - runner/prompts.py
  - docs/workflow.md
  - docs/agents/lead.md
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_prompts.py
---

### Goal
A retried or escalated ticket builds on the work already on its branch, unless the lead says it is unusable, and an escalation can finish the work itself.

### Context
Read `docs/adr/15-allowance-aware-routing.md` items 7 and 8, `docs/workflow.md` (the attempts: attempt 3 resets the branch), and in `runner/loop.py` `run_task` (`fresh_branch` at attempt 3), `give_direction`, `handle_escalation` and `_merge`; and `prompts.DIRECTED`, `prompts.FRESH`, `prompts.DIRECTION` and `prompts.ESCALATION` in `runner/prompts.py`. Test-first.
- **Evidence:** f1-34 spent $2.40 on 6 attempts and 2 escalations to land a 57-line fix: every retry after attempt 2, and every requeue, began again from main.
- **Attempt 3 and requeues continue on `task/<id>`** with the gate output. The branch resets to main only when:
  - the direction or escalation says so, in a `reset: true` line of its direction.md or in decision.json; or
  - the previous attempt timed out before its first edit.

  The prompts say which happened. A requeued ticket's branch is kept, not deleted, when it is escalated.
- **A new escalation outcome, `finish`:**
  - The lead checks out `task/<id>` (its job gets `Bash(git checkout:*)` for that branch only, or the runner checks it out before the job: choose and say which), finishes the work, and `check-all --task <id>` must pass.
  - The runner squash-merges it as `_merge` does. The commit and the ticket row credit both: `merged_by` the lead, and the developer in the commit's trailers.
  - The ESCALATION prompt lists `finish` first for a branch whose gates fail on a small, clear gap.
- Update `docs/workflow.md`'s attempts and lead.md's Escalations to match.

### Done when
- attempt 3 starts from attempt 2's work; with `reset: true` in the direction it starts from main
- an escalation answering `finish` on a fake branch merges it, with both agents credited, and the ticket moves to `done/`
- a requeued ticket's next run continues its branch
- `uv run runner check-all --task f1-47-build-on-and-finish` passes
