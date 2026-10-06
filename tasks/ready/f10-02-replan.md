---
id: f10-02-replan
milestone: f10-crates
depends_on: [f10-01-crate-per-job]
agent: lead
difficulty: 3
files:
  - docs/milestones/f10-crates.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
F10's doc matches what f10-01 built, and the small developer tickets for the crates' looks and the replay's motion are written in `tasks/ready/`.

### Context
Read `docs/milestones/f10-crates.md`, f10-01's merge (`git log`, `git show`), `docs/task-writing.md` and `docs/agents/lead.md` ("Replans", "Known range": F3 and F4).
- Each developer ticket is one small, picture-backed change on f10-01's core, with Done when bullets that say what each assertion must reject.

### Done when
- the doc's "Replan" section logs what changed and why
- each new ticket passes `uv run pytest -q tests/runner/test_tasks.py`
