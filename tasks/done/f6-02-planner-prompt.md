---
id: f6-02-planner-prompt
milestone: f6-planning-room
depends_on: [f6-01-planner-threads]
agent: lead
difficulty: 5
files:
  - runner/prompts.py
  - runner/planner.py
  - docs/agents/lead.md
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_prompts.py
---

### Goal
The planner plans the way the lead planned with the owner on 2026-10-02/03: numbered points, each with an answer and an action, proposals as drafts on the card's branch, and nothing queued without approval.

### Context
Read `docs/adr/20-planning-room.md`, D2 and D4 in `docs/milestones/f6-planning-room.md`, `docs/agents/lead.md` (The owner, Plan, Tickets: the planner follows them), `runner/prompts.py` (the other jobs' prompts) and `runner/planner.py` (f6-01).
- **The prompt says:**
  - answer the owner's questions first, then revise;
  - every reply ends with the JSON block (D2);
  - challenge the owner where there's a better option (lead.md);
  - drafts go on `plan/<card>` only: ADRs in `docs/adr/`, mock-ups as self-contained HTML in `docs/milestones/<card>-mockup/`, the milestone doc, tickets in `tasks/later/`;
  - every proposal lists its key points.
- **The tools:** read the repo and git, Edit on the plan branch's docs and tasks only, `git checkout plan/<card>`, never main. The runner commits the branch after the job.
- Add a short "Planning room" section to `docs/agents/lead.md` pointing at the prompt.

### Done when
- the prompt names the block, the branch and the approval rule (test on `prompts.PLANNER`)
- a fake planner job's edits land on `plan/<card>`, never on main, and are committed by the runner
- `uv run runner check-all --task f6-02-planner-prompt` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
