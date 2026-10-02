---
id: f2-02-claude-window
milestone: f2
depends_on: []
agent: lead
difficulty: 7
files:
  - runner/allowance.py
  - runner/copilot.py
  - runner/router.py
  - runner/loop.py
  - runner/config.py
  - workflow/runner.toml
  - docs/workflow.md
tests:
  - tests/runner/test_allowance.py
  - tests/runner/test_router.py
  - tests/runner/test_loop.py
  - tests/runner/test_config.py
---

### Goal
Unattended work keeps the last 25% of Claude's 5-hour window for the owner, lead work comes before Claude taking developer tickets, support roles park at a limit instead of holding up the queue, and Copilot does a checkpoint when Claude can't.

### Context
Read `docs/adr/16-claude-window-and-named-milestones.md` items 1–4 and 9, `docs/milestones/f2.md` D1 and D2, `docs/adr/15-allowance-aware-routing.md` items 1, 4, 5 and 10, then `runner/allowance.py` (`answer`, `reserve_only`), `runner/router.py` (`route`, `_developer`, `_reviewer`) and `runner/loop.py` (`claude_windows`, `agent_windows`, `route_developer`, `at_reserve`, `_at_the_reserve`, `call_claude`, `_park`, `_next_task`, `_limits_ahead`). Test-first.
- **What happened in F1:** at 05:26 on 2 Oct the router sent f1-28, f1-31 and f1-52 to `claude-sonnet` ("week 16% used, under its pace line of 35%"); the 5-hour reading went from 22% at 05:04 to 100% at 06:12 and lead ticket f1-53 parked. `claude_windows` gives the `five_hour` window no reserve, and a rolling window is a plain cap at 100%.
- **The 25%:** `claude_windows` sets the `five_hour` window's reserve from `[claude] five_hour_reserve`; a rolling window with a reserve caps at `capacity − reserve` unless `use_reserve`. This applies to every Claude job, support roles included (ADR 16 item 4 amends ADR 15 item 4 for this window only).
- **The question:** when the only runnable work is refused by the 5-hour reserve alone, ask once per command, like `at_reserve` does for the week, with its own text and its own yes: `Claude's 5-hour window is at 76% (resets 14:50), kept for you. Use it for this run? [y/N]`. A yes to the week doesn't answer it, nor the reverse. No answer: parked, a Needs-you item of its own kind.
- **Lead first:** in `route`, a Claude developer is permitted only when no lead work is ready (the caller says so: a ready lead ticket, a direction or escalation due, or a checkpoint due) and the 5-hour window is under `[claude] developer_five_hour_cap`. Otherwise the next permitted agent takes it, local at worst.
- **Support roles park:** checkpoints, escalations and reviews refused by a limit (or by the 25%) park as lead tickets and directions do (`_park`, `park=True`), so `_next_task` can run developer tickets meanwhile; they resume first after the reset.
- **The question never blocks** (item 3): asked only when nothing else can run; a yes lets the parked work go; no answer, and it goes by itself at the window's reset.
- **Copilot steps in** (item 9): a checkpoint due while Claude is past 75% (or refused) goes to `copilot-auto` (`runner/copilot.py`'s adapter, read-only), acted on like Claude's: its findings become fix tickets. For that job Copilot's month is a cap at its capacity, not its pace line.
- Update `docs/workflow.md` where it describes the reserve.

**The last line that matters:** a test with readings of 80% on `five_hour` and 10% on `seven_day` must route a developer ticket away from Claude and park a lead ticket, with no question asked when another ticket can run.

### Done when
- at 70% of the 5-hour window a lead ticket runs; at 80% it parks, and the 5-hour question is asked only when nothing else can run
- with a lead ticket ready, a developer ticket never goes to a Claude agent; with none ready and the window at 40%, it may
- a checkpoint refused by a limit parks and the queue goes on with a developer ticket
- a yes to the week's reserve doesn't lift the 5-hour reserve
- with Claude at 80%, a due checkpoint runs on `copilot-auto` and its findings are acted on
- `uv run runner check-all --task f2-02-claude-window` passes
