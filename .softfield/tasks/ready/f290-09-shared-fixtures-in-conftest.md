---
id: f290-09-shared-fixtures-in-conftest
milestone: f290-runner-loop-py-is-6-500
difficulty: 3
depends_on: []
finding: f290-runner-loop-py-is-6-500-F1
tests_only: true
area: factory
files:
  - tests/runner/conftest.py
  - tests/runner/test_loop.py
  - tests/runner/test_session.py
  - tests/runner/test_waits.py
  - tests/runner/test_developer_job.py
  - tests/runner/test_lead_job.py
  - tests/runner/test_rating_store.py
  - tests/runner/test_review_job.py
  - tests/runner/test_backup.py
tests:
  - tests/runner/test_session.py
  - tests/runner/test_waits.py
  - tests/runner/test_backup.py
---

### Goal
The two autouse fixtures every runner test file needs (`_new_command` and `_no_probe`) live in `tests/runner/conftest.py`, so no test file imports a fixture from `tests/runner/test_loop.py`.

### Context
- `tests/runner/test_loop.py` defines `_new_command` (empties `session.OPEN_RUNS`) and `_no_probe` (stubs `waits.fresh_reading`), both `@pytest.fixture(autouse=True)`. Six files import them from there with `# noqa: F401 - _new_command and _no_probe are fixtures`: `tests/runner/test_session.py`, `tests/runner/test_waits.py`, `tests/runner/test_developer_job.py`, `tests/runner/test_lead_job.py`, `tests/runner/test_rating_store.py`, `tests/runner/test_review_job.py`.
- The card's D6 (`.softfield/cards/f290-runner-loop-py-is-6-500.md`) says a fixture used by more than one file goes to `tests/runner/conftest.py`; `fake_clock` and `at_the_keyboard` already moved there.
- `tests/runner/test_backup.py` has `_quiet_run`, the same two patches under another name: delete it.
- `REAL_FRESH_READING` stays in `tests/runner/test_loop.py` (only it uses it).
- Move only: no test's name or body changes, apart from the imports you drop. Other names those six files import from `tests/runner/test_loop.py` (helpers such as `_config`, and `fake_model`) stay imported as they are.

### Done when
- `_new_command` and `_no_probe` are defined once, in `tests/runner/conftest.py`, and no file imports either one.
- `tests/runner/test_backup.py` has no `_quiet_run`.
- No `noqa: F401` comment in `tests/runner/` mentions `_new_command` or `_no_probe`.
- Every test in `tests/runner/` passes, with the same names as before.
