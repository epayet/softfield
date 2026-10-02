---
id: f2-04-job-model
milestone: f2
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/metrics.py
  - runner/claude.py
  - runner/local_model.py
  - runner/copilot.py
  - runner/loop.py
  - runner/backfill.py
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_claude.py
  - tests/runner/test_local_model.py
  - tests/runner/test_backfill.py
---

### Goal
Every job records the exact model it ran on, so a new Sonnet can be compared with the old one.

### Context
Read `docs/adr/16-claude-window-and-named-milestones.md` item 5 and `docs/milestones/f2.md` D3, then `runner/metrics.py` (`MIGRATIONS`, the `jobs` table, `start_job`, `finish_job`), `runner/claude.py` (`_parse_stream`), `runner/local_model.py` (`OpencodeAdapter`), `runner/copilot.py` and `runner/backfill.py`. Test-first.
- Claude's stream-json names the model on its `system`/`assistant` events: `var/runs/20261002-055804/claude-lead-ticket-f1-53-factory-line.log` has `"model":"claude-opus-5-5"`. Use what the stream says, not the config's alias (`sonnet`, `opus`).
- OpenCode jobs: the agent's `model` from `workflow/runner.toml` (`lmstudio/qwen/qwen3.6-35b-a3b`, `ollama/gpt-oss:120b-cloud`). Copilot: `auto` unless its output names one.
- A new migration adds `jobs.model TEXT`; earlier rows stay empty unless backfill reads it from a job's `log_path`.

### Done when
- a Claude job's row has the model its stream named; an OpenCode job's, its agent's model
- backfill fills `model` for past Claude jobs whose logs still exist, and running it twice changes nothing
- `uv run runner check-all --task f2-04-job-model` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
