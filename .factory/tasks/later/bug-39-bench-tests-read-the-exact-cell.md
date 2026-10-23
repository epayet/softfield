---
id: bug-39-bench-tests-read-the-exact-cell
milestone: bugs
difficulty: 2
depends_on: []
area: factory
priority: 67
finding: f1-C165-2
tests_only: true
files:
  - tests/factory_dashboard/test_bench.py
  - tests/factory_dashboard/test_eligibility.py
tests:
  - tests/factory_dashboard/test_bench.py
  - tests/factory_dashboard/test_eligibility.py
---

### Goal
The Bench and Eligibility page tests read the exact cell they mean, not a substring anywhere on the page.

### Context
Read `tests/factory_dashboard/test_bench.py` and `tests/factory_dashboard/test_eligibility.py`: their page tests check that a word is in the response text. The code is right; the tests are weak (f1-C165-2, f1-S166-2 and 3).
- Cut out the row (the ticket's on Bench, the agent's on Eligibility) and its column, then assert that cell's text.

### Done when
- each assertion names its row and column: on Bench, the cell of a ticket and an agent; on Eligibility, the eligible row's status column
- an assertion fails if the expected word is moved to another row or column (check each by editing the fixture once, by hand, and putting it back)
- no test loses a case it has today
- all gates pass (see `docs/workflow.md`)
