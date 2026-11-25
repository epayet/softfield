---
id: f290-03-replan-after-the-base
agent: lead
milestone: f290-runner-loop-py-is-6-500
difficulty: 3
depends_on: [f290-02-waits-own-module]
files:
  - .softfield/cards/f290-runner-loop-py-is-6-500.md
  - runner/session.py
  - runner/waits.py
  - .softfield/tasks/ready/f290-04-developer-job-own-module.md
  - .softfield/tasks/ready/f290-05-lead-job-own-module.md
  - .softfield/tasks/ready/f290-06-rating-store-own-module.md
  - .softfield/tasks/ready/f290-07-review-job-own-module.md
  - .softfield/tasks/ready/f290-08-planner-job-own-module.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
The five moves left fit what f290-01 and f290-02 built: their Decisions, function lists and patch targets are checked against `runner/session.py` and `runner/waits.py`, fixed where wrong, and what was found is logged in the card doc (ADR 16 item 7).

### Context
Read the Decisions in `.softfield/cards/f290-runner-loop-py-is-6-500.md`, the two commits (`git log -2 --stat`) and their reviews' notes if any, then `runner/loop.py`, `runner/session.py` and `runner/waits.py` as they stand.
- For each of f290-04 to f290-08: is every function its Context names still in `runner/loop.py`, or did 01 or 02 take it? Does a helper it needs now sit in `runner/session.py` as D3 says? Are its `files:` the modules and tests that import the names it moves (Grep for them)? Is its `max_diff` at least twice the lines it moves, plus its tests?
- Check D5's list of patched names against `tests/runner/` as it stands, and D8's sizes against what 01 and 02 landed; change a Decision only to match what was built, and say why.
- Change only docs and tickets: no code.
- Log what you checked and changed under `## Replan (f290-03)` in the card doc, one line each, as `.softfield/cards/f143-split-test-planning-py-by-page.md` does under its Replan.

### Done when
- every `def` and `class` the five tickets name sits where their Context says
- `## Replan (f290-03)` in the card doc lists each ticket checked and what changed, or "unchanged"
- `tests/runner/test_tasks.py` passes, so every ready ticket passes pre-flight
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
