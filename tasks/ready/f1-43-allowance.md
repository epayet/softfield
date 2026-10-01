---
id: f1-43-allowance
milestone: f1
depends_on: [f1-17-difficulty]
agent: lead
difficulty: 6
files:
  - runner/allowance.py
tests:
  - tests/runner/test_allowance.py
---

### Goal
One pure function answers, for any agent, "may it take a job of expected cost `c` now?", from its windows, learned capacities and Claude's reserve.

### Context
Read `docs/adr/15-allowance-aware-routing.md` items 1, 2, 4 and 5 (Accepted). Test-first, with table tests. The module does no IO: windows, readings, refusals, past job costs and the time are parameters, and the callers (f1-44, f1-46, f1-25) read the database.
- **Windows:** a kind (`rolling` or `fixed`), a length, a reset time, a capacity (learned, or unknown), the usage so far, and a reserve (Claude's weekly window only: 30%, from `[claude]` in `workflow/runner.toml`).
  - **Claude's** windows come with readings as fractions of 1 (f1-44): its capacity is 1.0 and `c` is a fraction.
  - **Ollama and Copilot** count tokens or requests.
- **The rule (item 1):**
  - spread on fixed windows; sweep in their last 10%; a cap on rolling windows
  - every window must agree
  - an agent with no windows (local) always passes
  - `answer(...)` returns the decision and a one-line reason for the job's `routing_reason`, for example "claude-sonnet: week 41% used, under its pace line of 52%"
- **Learning (item 2):**
  - a refusal sets the capacity at the usage it came at
  - in the sweep, an agent may go past its learned capacity
  - unknown capacity means "until refused", then a cooldown: until the reset, or 1 h then the next window when no reset is given
  - infer a window's kind from how far ahead its resets are: hours means rolling, days means fixed
- **`expected_cost(agent, difficulty, past_jobs)`:** the median of that agent's past jobs at that difficulty. Fall back to all its jobs, then to a seed from config.
- **The reserve question (item 5):** a separate function says whether a refusal was *only* because of the reserve. The caller (f1-46) asks the owner then.

### Done when
- table tests cover: under and over the pace line; the sweep allowing what spread refuses; a rolling cap; two windows where the tightest wins; local always passing; a refusal lowering capacity; passing the learned capacity in the sweep; the unknown-capacity cooldown; the reserve-only refusal
- the 2026-10-01 probe (`tests/runner/fixtures/probes/claude-stream.jsonl`: week 79% used, resets Monday 17:00) refuses a developer job on Thursday and allows a review
- `uv run runner check-all --task f1-43-allowance` passes
