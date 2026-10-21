---
id: f71-02-slow-tests-study
milestone: f71-i-suspect-we-might-need-to
difficulty: 4
depends_on: [f95-02-lead-jobs-can-look]
agent: lead
commands: [softfield look]
files:
  - .factory/cards/f71-i-suspect-we-might-need-to.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
Find where the test suite's time goes and propose steps that make it faster without dropping a test.

### Context
Read `.factory/cards/f71-i-suspect-we-might-need-to.md` (D3 lists the questions), `runner/checks.py` (`check_all`), `runner/gates.py` (`gate_all_tests`, `gate_tests_fail_on_main`), `pyproject.toml` (`[tool.pytest.ini_options]`), `tests/layout.py`, `tests/factory_dashboard/conftest.py` and `.factory/adr/21-gate-every-test-file.md`.
- The suite stays as thorough: the developers lean on it. Faster means running it better, not testing less.
- Measure on main with `uv run pytest --durations=30` over the same directories as `gate_all_tests`, and time each directory and `mypy` on their own.
- Also the card's "What we saw on 2026-10-13" and D7: two more steps to give a verdict on, the quick checks first with an answer at once when one fails, and the developer's prompt not setting a time limit on `check-all`. D1's limit is D5's now (75 minutes).
- **Change no code or config: findings and proposals only.**

### Done when
- the card has a "Findings" section: the suite's total, each directory's and `mypy`'s time, the 30 slowest tests grouped by cause, and how many full runs one ticket costs
- Findings also say, from the jobs table (`softfield look sql "SELECT …"`, read-only; `runner/metrics.py` has the schema): how long developer attempts and Claude jobs took over the last two weeks, how many were cut off, and whether D1's and D2's limits fit (D4); a limit to change is a follow-up ticket, not a later look
- each of D3's steps has a verdict (do, don't, later) with its measured or estimated saving in minutes per ticket and its risk
- every "do" step is a ticket in `.factory/tasks/later/` (developer when unprotected and on an existing pattern); one that changes a gate or the workflow is a draft ADR in `.factory/adr/`, status Proposed
- the tickets it writes pass `uv run pytest -q tests/runner/test_tasks.py`
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
note: done by the lead in a terminal session with the owner on 2026-10-21; its findings are on the card, and the suite runs on 16 workers
```
