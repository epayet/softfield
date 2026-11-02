---
id: bug-05-idle-restart-waits-for-a-commit
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 25
finding: f101-uv-runner-run-command-stopped-when-F4
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
An idle `softfield run` restarts onto new runner code only once that code is committed, never on a half-saved change.

### Context
Read `def _runner_code` and `def work_queue` in `runner/loop.py`, and the tests beside F101's idle restart in `tests/runner/test_loop.py`. `runner/**` is protected: write the tests first, each failing for the right reason.
- Today an idle run reads `runner/`'s fingerprint every 5 seconds and restarts as soon as it differs, committed or not. A terminal session half-way through a change spread over two files restarts the standing runner onto code that may not import, and it dies with nobody at the terminal.
- The new rule: while idle, restart only when `runner/` is clean in git (`git status --porcelain -- runner/` is empty) and the fingerprint differs from the one the process started with.

### Done when
- an idle run with an uncommitted change under `runner/` doesn't restart, however long it waits
- once that change is committed, the run restarts within one poll
- a change committed and then reverted to the start's code doesn't restart it
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
