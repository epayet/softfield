---
id: f1-42-console-log
milestone: f1
depends_on: []
agent: lead
difficulty: 4
files:
  - runner/console.py
  - runner/loop.py
  - runner/milestone.py
  - runner/local_model.py
tests:
  - tests/runner/test_console.py
  - tests/runner/test_loop.py
---

### Goal
`runner milestone` tells the owner, as it happens, which agent is doing what, how each job ended, and what is blocked, in a few readable lines per ticket.

### Context
The owner watched f1 from the terminal and asked for this (2026-10-01). Read `runner/loop.py` (`Session.log` and its 10 call sites, `call_claude`, `run_task`, `run_lead_task`, `checkpoint`, `handle_escalation`, `block`, `live_update`), `runner/milestone.py` (`review_milestone`, `run_e2e`'s call) and `docs/adr/15-allowance-aware-routing.md` item 14. Test-first.
- **Today:** a ticket prints only its goal and its end; a Claude job prints nothing while it runs (a 30-minute review looked hung, and the owner stopped it), and a blocked ticket is one line before the runner moves on.
- **Pure formatters** in a new `runner/console.py` (tests in `tests/runner/test_console.py`). `runner/loop.py` and `runner/milestone.py` call them through `Session.log`. Every line names its agent in brackets, for example `[local-qwen3.6-35b-a3b]`, `[claude-opus]`, `[claude-sonnet]`, `[runner]`.
- **What to print:**
  - **A ticket or milestone job starts:** a blank line, then a header (`── f1-15-agents-page · developer · d6 ──`), then its goal.
  - **Each job:** a start line (`▶ [local-qwen3.6-35b-a3b] attempt 1/3`, `▶ [claude-opus] direction`) and an end line with the outcome, minutes, and tokens and steps (local) or dollars (Claude). A failed gate is named.
  - **Claude jobs' end line:** add one line on what the job did, taken from the note it already writes (escalation.md, direction.md, checkpoint-N.md, decision.json's outcome), or else the first line of its result text, cut to about 100 characters.
  - **While running:** one progress line every 10 minutes, for local attempts (from `live_update`'s ticks: minutes, tokens, steps, edit streak), for Claude jobs (elapsed only) and for the e2e run.
  - **Merges:** the merger, its attempts, lines changed and duration.
  - **Blocked or escalated:** printed at once with `⚠`, the reason, where the work is, and how many tickets wait behind it (`blocked_ids` in `runner/tasks.py`).
  - **Pauses:** the limit and the exact resume time, for example `⏸ [claude-opus] Claude session limit · resumes 18:51 (in 12 min)`, and a line when the job resumes.
- **Budget:** about 5–8 lines for a ticket that merges at the first attempt; no line per tool call or per gate that passes.
- Claude jobs still run with `--output-format json` (f1-44 changes that), so their progress line is a timer: a thread or the `subprocess.run` timeout in short slices, whichever is simpler to test.

### Done when
- a fake ticket run through the loop prints its header, an attempt start, its end with the agent, and a merge line naming the merger
- a blocked lead ticket prints `⚠` with the number of tickets waiting behind it, before anything else runs
- a fake Claude job longer than 10 minutes (an injected clock) prints a progress line
- a usage-limit pause prints the resume time
- `uv run runner check-all --task f1-42-console-log` passes
