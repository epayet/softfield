---
id: bug-44-remove-the-folded-f9-12-ticket
milestone: bugs
difficulty: 1
depends_on: []
agent: lead
area: factory
priority: 72
finding: f8-one-queue-F6
commands: [rm .factory/tasks/later/f9-12-fix-the-desktop-test-does.md]
files:
  - .factory/cards/f9-line-polish.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
The set-aside ticket f9-12, whose finding f8-09 folded into f9-11, is gone.

### Context
f8-09 folded f9-12's finding into f9-11 ("so 12 goes", F9's doc), but a headless job can't delete files, so `.factory/tasks/later/f9-12-fix-the-desktop-test-does.md` stayed.
- Check that F9's doc and f9-11 say the finding is f9-11's; then delete the file with `rm .factory/tasks/later/f9-12-fix-the-desktop-test-does.md`.

### Done when
- the file is gone, and no ready or later ticket depends on `f9-12-fix-the-desktop-test-does`
- `uv run pytest -q tests/runner/test_tasks.py` passes
