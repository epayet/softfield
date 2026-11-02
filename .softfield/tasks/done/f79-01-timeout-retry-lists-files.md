---
id: f79-01-timeout-retry-lists-files
milestone: f79-when-a-task-times-out-on
difficulty: 3
depends_on: []
agent: lead
area: factory
files:
  - runner/loop.py
  - runner/prompts.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A retry after a timed-out attempt names the files that attempt changed, so the developer picks up its work instead of rediscovering it.

### Context
- `runner/loop.py`: `_prompt` adds `prompts.TIMED_OUT` when the attempt before timed out and the branch was kept; `run_task`'s attempt loop calls it. A requeued ticket's first attempt already lists the earlier run's files (`prompts.EARLIER`, from `s.git.changed_files(MAIN)`): follow that.
- `runner/prompts.py`: `TIMED_OUT`, `EARLIER`.
- Why: a developer on OpenCode may run only the check commands, not `git diff`, so a fresh session can't see what its timed-out attempt did except by reading files one by one.
- Worked example: `test_a_retry_after_a_timeout_says_so` in `tests/runner/test_loop.py`.

### Done when
- After a timed-out attempt whose work was kept, the next prompt says it ran out of time and lists the files changed against main, comma-separated.
- After a timeout before the first edit (branch reset to main), the prompt lists no files and says the branch was reset, as now.
- A retry after an ordinary gate failure is unchanged.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
