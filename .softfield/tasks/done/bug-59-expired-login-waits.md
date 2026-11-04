---
id: bug-59-expired-login-waits
milestone: bugs
difficulty: 5
depends_on: []
agent: lead
area: factory
priority: 1
files:
  - runner/claude.py
  - runner/loop.py
tests:
  - tests/runner/test_claude.py
  - tests/runner/test_loop.py
---

### Goal
When Claude's login has expired, the runner holds Claude's jobs and asks the owner to log in, instead of failing them, and starts them again by itself once the login works.

### Context
On 2026-11-04 the login expired during f203-03. Each `claude -p` then answered in under a second with `is_error` true, `terminal_reason` "api_error", `api_error_status` null and the result "Failed to authenticate: OAuth session expired and could not be refreshed" (`.softfield/var/runs/20261104-101952/claude-probe.log`). The runner took that for a passing error: each job waited through three retries, about 21 minutes, then failed. In three hours it blocked f203-03 and f162-01 ("the lead ticket changed nothing", though it never ran) and failed the lead's look at f203-03's block.

Read `run_claude`, `_transient`, `TransientError`, `UsageLimited` and `probe` in `runner/claude.py`, then `_park`, `park_row` and `_queue_parked` in `runner/loop.py`: a limit is the example to follow, since it already holds a job without using up an attempt. Match the words "Failed to authenticate" in the result, as `usage_limit_reset` matches a limit's. The check is only as good as that wording, so a test pins it with the real result line above.

The desk item says what to do in words, with no terminal command (`command=""`): "Claude's login has expired: log in again on this machine."

### Done when
- a job answering with the result line above raises its own error in `run_claude`, not `TransientError`, and a test with that exact line shows it
- a lead ticket stopped this way stays in `ready/`, with no attempt counted and no ticket blocked
- a planner job stopped this way keeps its queue row open, and no "the lead's job failed" message goes on its thread
- one item goes on the desk however many jobs were stopped, and the owner is notified once
- developer tickets still run while the login is out
- at each pick the runner probes, at most every 5 minutes, and a passing probe clears the item and frees the held jobs, with no restart
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
