---
id: f1-44-claude-readings
milestone: f1
depends_on: [f1-42-console-log, f1-43-allowance]
agent: lead
difficulty: 6
files:
  - runner/claude.py
  - runner/loop.py
  - runner/metrics.py
  - runner/config.py
  - workflow/runner.toml
tests:
  - tests/runner/test_claude.py
  - tests/runner/test_metrics.py
  - tests/runner/test_loop.py
---

### Goal
Every headless Claude job records Claude's allowance as it goes: how much of the 5-hour and weekly windows is used, and when each resets.

### Context
Read `docs/adr/15-allowance-aware-routing.md` (Context's probe, items 3 and 4), `runner/claude.py` (`run_claude`, `usage_limit_reset`, `TransientError`) and `runner/metrics.py` (`usage_events`, `add_usage_event`, `MIGRATIONS`). Test-first.
- **The probe** (2026-10-01, Claude Code 2.1.286) is saved as `tests/runner/fixtures/probes/claude-stream.jsonl`: with `--output-format stream-json --verbose`, the stream has a `rate_limit_event`, whose `rate_limit_info.unifiedWindows` holds `five_hour` and `seven_day`, each with `utilization` (0–1) and `resetsAt` (epoch seconds). Its last line is the `result` event, with the same fields today's `--output-format json` returns (`result`, `is_error`, `api_error_status`, `session_id`, `usage`, `total_cost_usd`).
- **`run_claude`** switches to stream-json. It reads the `result` event exactly as it reads today's JSON, so limits, transient errors and costs behave as now. It also returns every `rate_limit_event` it saw. The log keeps the whole stream.
- **The loop** writes each window as a `usage_events` row of kind `reading`: the agent, the window name, its utilization as `value`, and `resets_at` as an ISO time. A 429 refusal records the window its `rateLimitType` names when there is one. The table's key is (agent, at, kind), so two windows read at the same moment collide: add a `window` column in a new migration, and keep writes idempotent.
- **Config:** `[claude] reserve = 0.3` (ADR 15 item 4), read into `Config`. `usage_limit_backoff_max` stays for unsure limits.
- **The Overview's Claude bar** (`claude_allowance` in `factory_dashboard/overview.py`) keeps working on refusals. A later dashboard ticket switches it to readings: leave it.

### Done when
- the probe's stream gives two readings (`five_hour` 0.07, `seven_day` 0.79) with their reset times, and the same result, cost and session as before
- a 429 in a stream still raises `UsageLimited` with its session, and a stream with no result event is transient
- a job run through the loop writes its readings; writing the same readings twice changes nothing
- `uv run runner check-all --task f1-44-claude-readings` passes
