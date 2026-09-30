---
id: f1-02-runner-writes-jobs
milestone: f1
depends_on: [f1-01-metrics-db]
agent: lead
difficulty: 7
files:
  - runner/loop.py
  - runner/local_model.py
  - runner/claude.py
  - runner/metrics.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_local_model.py
  - tests/runner/test_claude.py
---

### Goal
The runner writes each run and each job to the metrics database as it happens, so a crash loses nothing and the dashboard can show what's running now.

### Context
Read `docs/milestones/f1.md` (D2, D3, D6) and `runner/metrics.py`. Test-first; the loop tests already fake OpenCode and Claude (`tests/runner/test_loop.py`), so assert on the rows in a `tmp_path` database set through the config.
- **Runs:** a row at session start (`command`, `started`, `heartbeat`), finished at the end with its verdict.
- **Local attempts:** a job row at the start of each attempt (`role` `developer`, or `last-attempt` for the directed one; `agent` `local-qwen3.6-35b-a3b` from the configured model), finished with the outcome (`passed`, `failed`, `timeout`), tokens, steps, peak context and the loaded context limit, the edit streak, refused commands, the gates as JSON with seconds and log paths, the session id and log path. `runner/local_model.py`'s `stream_facts` and `parse_events` already compute most of it.
- **Live:** `run_opencode` reads the stream line by line into its log (today it collects the output at the end), and every 30 s the loop updates the running job's tokens and steps and the run's `heartbeat`. Keep the time source a parameter so tests don't sleep.
- **Claude jobs:** every `call_claude` writes a job with its role (D6: `direction`, `escalation`, `checkpoint`, `lead-ticket`, `review`, `narrative`), agent (`claude-opus`, or `claude-sonnet` when the job's model is the checkpoint model), time, usage and `cost_usd` (the JSON's `total_cost_usd`, which `runner/claude.py` doesn't read yet).
- **One log per Claude job:** today a second escalation of the same ticket overwrites `claude-escalation-<id>.log`; number them.
- **Limit pauses** become `usage_events` (`refusal`, with `resets_at`).
- **The database is best effort:** a write that fails is logged once in the session report and never stops the run.

### Done when
- a session with one passing and one failing attempt leaves a run and two finished jobs with their gates, tokens and outcomes
- a job interrupted mid-run (the fake OpenCode raises) stays `running`, and the run's heartbeat is set
- a live update changes tokens, steps and heartbeat, and nothing else
- each Claude job kind writes a row with its role, agent and `cost_usd`, and two escalations of one ticket keep two logs
- a usage-limit pause writes a `refusal` event with its reset time
- a database that can't be opened doesn't stop the session
- `uv run runner check-all --task f1-02-runner-writes-jobs` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
