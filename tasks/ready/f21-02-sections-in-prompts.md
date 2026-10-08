---
id: f21-02-sections-in-prompts
milestone: f21-lead-briefs
difficulty: 4
depends_on: []
agent: lead
files:
  - runner/prompts.py
  - runner/loop.py
tests:
  - tests/runner/test_prompts.py
  - tests/runner/test_loop.py
priority: 0
---

### Goal
Every lead job's prompt starts with `docs/agents/owner.md` and the `docs/agents/lead.md` sections its role needs, pasted in, instead of pointing at the files.

### Context
Read `docs/milestones/f21-lead-briefs.md` (D2: the role-to-sections table, the missing-heading rule, no sections on a resumed planner session), `runner/prompts.py` (each prompt constant D2 names, and the "lead.md" pointers in them), `runner/loop.py` (where each lead role's `JobSpec` is built: `run_planner`, `call_claude`'s callers), and `docs/agents/lead.md`'s `## ` headings.
- The sections go first in the prompt, the same text for every job of a role, so jobs close together share Claude's prompt cache.
- **A test reads the real `docs/agents/lead.md` and fails when a heading in the map is missing, so a renamed section is caught at commit, not in a run.**

### Done when
- a planner job's first prompt starts with owner.md's text, then Authority, Plan, Planning room and Tickets, and holds no other lead.md section
- a planner job resuming a session gets no sections
- a lead ticket, an escalation, a direction, a checkpoint and a review each get owner.md plus exactly their D2 sections
- the prompts no longer say "as docs/agents/lead.md says"
- a heading missing from lead.md: the job runs with what was found, and the session report has a note
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
