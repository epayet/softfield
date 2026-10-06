---
id: f8-09-stand-in-fix-tickets
milestone: f8-one-queue
depends_on: []
agent: lead
difficulty: 6
files:
  - runner/prompts.py
  - runner/loop.py
  - runner/tasks.py
  - runner/gates.py
  - docs/task-format.md
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_tasks.py
---

### Goal
A stand-in checkpoint files few, useful fix tickets that the local model can do: one per merged ticket and kind of fix, and a weak test is a developer's test-only ticket, not an escalation.

### Context
Read `CHECKPOINT_STAND_IN` in `runner/prompts.py`, `stand_in_checkpoint` and `fix_ticket` in `runner/loop.py`, the tests-only pre-flight in `runner/tasks.py` and the `tests-fail-on-main` gate in `runner/gates.py`. Test-first.
- What went wrong (2026-10-05): Copilot's two checkpoints filed 7 tickets; 5 list only a test (`files:` from the finding's file), so pre-flight sends each to Claude: a lead job per weak assertion. They wait in `tasks/later/`: f9-06, f9-07, f9-10, f9-11, f9-12.
- The prompt asks: the fix's kind, `code` (name the code file at fault, and quote the ticket line it breaks) or `test` (the code is right, the test is weak); one entry per merged ticket and kind; no nits. Its example path is a real repo-relative one (f4-25…29 copied its example, coucou/x.py, as a prefix).
- `fix_ticket` writes one ticket per (merged ticket, kind), every finding quoted in it. A `test` ticket says so in its frontmatter (document the field in `docs/task-format.md`); pre-flight lets it through and `tests-fail-on-main` is skipped for it. f8-08's re-check is what checks it.
- Then rewrite the five waiting tickets as test-only tickets (two: f9-06/07 on f4-39 and f3-28, and one per f3-29, f3-30) and queue them.

### Done when
- three test findings and one code finding on one merged ticket give two tickets, the test one test-only
- a test-only ticket passes pre-flight and merges with tests that pass on main; any other ticket still needs them to fail
- `uv run runner check-all --task f8-09-stand-in-fix-tickets` passes
