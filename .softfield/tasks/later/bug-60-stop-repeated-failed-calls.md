---
id: bug-60-stop-repeated-failed-calls
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
finding: f192-when-i-click-use-the-fast-F8
files:
  - runner/local_model.py
tests:
  - tests/runner/test_local_model.py
---

### Goal
A local attempt that keeps making the same failing tool call is stopped early, with a stop reason saying so, instead of running on until its timeout.

### Context
`stuck` in `runner/local_model.py` stops an attempt for no edit after 20 minutes, or for reasoning that repeats one phrase, but not for failing calls. f192-03's last attempt ran 30 minutes while looping on an edit call with no `filePath`, and its log has 13 lines matching a failed call. Read how `stream_facts` reads the lines, and add a stop in `stuck` beside `STOP_REPEATING`, listed in `STOP_REASONS`, for a number of failed calls in a row with the same error. Its `test_local_model.py` cases for `stuck` are the worked example.

### Done when
- five failed calls in a row with the same error: `stuck` returns the new stop reason
- five failed calls with different errors, or with a successful call among them: `stuck` returns ""
- `stop_reason` recognises the new reason
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
