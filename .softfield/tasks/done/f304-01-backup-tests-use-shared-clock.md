---
id: f304-01-backup-tests-use-shared-clock
milestone: f304-simpler-tests-runner-test-backup-py
difficulty: 2
depends_on: []
tests_only: true
area: factory
files:
  - tests/runner/test_backup.py
tests:
  - tests/runner/test_backup.py
---

### Goal
`tests/runner/test_backup.py` uses the shared `fake_clock` fixture and `THURSDAY` constant from `tests/runner/conftest.py` instead of its own copies.

### Context
- `tests/runner/conftest.py` defines `THURSDAY` and the `fake_clock` fixture (F290 D6: a fixture used by more than one file lives there). `tests/runner/test_backup.py` repeats both: `THURSDAY` near the top and `fake_clock` under the "the run" section heading.
- The shared fixture also keeps `subprocess`'s own sleep real; the backup tests don't rely on the difference.
- `tests/runner/test_backup.py` already imports `git` and `write_task` from `tests.runner.conftest`: import `THURSDAY` there too. `fake_clock` needs no import (pytest finds it in `tests/runner/conftest.py`).
- Drop any import that becomes unused (ruff will say which).
- No test's name or body changes.

### Done when
- `tests/runner/test_backup.py` defines neither `THURSDAY` nor `fake_clock`.
- Every test in `tests/runner/test_backup.py` passes, with the same names as before.
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 367
gate_failures: []
tokens: 231634
```
