---
id: f4-33-finding-tickets
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 3
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A checkpoint finding's fix ticket belongs to the milestone of the ticket at fault, and names only files that exist in the repo.

### Context
Read `fix_ticket` and its caller in `runner/loop.py` (the stand-in checkpoint), `short_key` and `full_key` in `runner/tasks.py`, and the `fix_ticket` tests in `tests/runner/test_loop.py`. Test-first.
- **What happened (2026-10-03, Copilot standing in at checkpoints 228 and 231):**
  - **Wrong milestone:** f4-21, f4-22 and f4-23 fixed findings on F3 tickets (f3-03) but were filed as F4 tickets, because `fix_ticket` takes the running checkpoint's milestone. The owner asked why F4, "always on", was doing factory-line work.
  - **Wrong paths:** f4-25 … f4-29 named `coucou/factory_dashboard/…` and `coucou/tests/…`. The finding's path started with the repo's directory name, and `_FIX_PATH_RE` only checks the path's shape. Pre-flight doesn't catch it either: a path in `files:` may be new. A developer would have created stray copies. The lead fixed the five tickets by hand.
- **The milestone:** take the at-fault ticket's own `milestone` (its `tasks/done/` file, already parsed as `source`), and number the new ticket in that milestone's series. Keep the running milestone when the at-fault one is signed off: its doc says "Status: done".
- **The path:**
  - If `repo / file` doesn't exist and its first part is the repo directory's name, drop that part.
  - If it still doesn't exist, use the at-fault ticket's `files` (as when the finding names no file), and say in the ticket's Context which path the finding named.

### Done when
- a test: a finding on an F3 ticket raised at an F4 checkpoint gives an `f3-NN-fix-…` ticket with F3's milestone
- a test: a finding naming `<repo name>/factory_dashboard/x.py`, where `factory_dashboard/x.py` exists, gives `files: [factory_dashboard/x.py]`
- a test: a finding naming a missing path gives the at-fault ticket's files, and the Context names the missing path
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
