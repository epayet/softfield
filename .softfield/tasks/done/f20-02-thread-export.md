---
id: f20-02-thread-export
milestone: f20-data-safety
difficulty: 4
depends_on: []
agent: lead
files:
  - runner/requests.py
  - runner/planner.py
tests:
  - tests/runner/test_planner.py
---

### Goal
Approving a card's plan also commits its whole planning thread to `docs/planning/<card's full key>.md`, in the same commit as the drafts.

### Context
Read `docs/milestones/f20-data-safety.md` (D2 is the file's content and when it is written), `runner/requests.py` (`_approve_plan`, the one commit it makes), `runner/metrics.py` (`planner_thread`, `planner_messages`), and `runner/planner.py` (`history`: the same messages put into words for a prompt; the export is for a person reading the repo).
- The tests to extend are the approval tests in `tests/runner/test_planner.py` (look for `approve_plan`).
- **The export is part of the approval's commit: a refused approval writes nothing, and main stays as it was.**

### Done when
- approving F7's plan commits `docs/planning/f7-<slug>.md` in the same commit as its drafts, with each message in order, its author and time, the lead's numbered points (title, answer, action), the owner's comments by point, and each proposal's title and kind
- a second approval on the same thread rewrites the file with every message to date
- an approval refused (a ticket failing pre-flight) leaves no `docs/planning/` file
- the general thread's approved merges write no file
- a message holding Markdown (`# x`, a backtick) can't break the file's headings
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
