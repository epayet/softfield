# Milestone F138: Run again right after Ctrl-C, without the 2-minute refusal

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-15.

## Notes
From the terminal session of 2026-10-15.

After Ctrl-C on `softfield run`, running it again says "runner: a run is live already (softfield): one runner at a time" for up to 2 minutes. The owner thought the runner was stuck.

Why: `softfield run` refuses while any project's run has a heartbeat under `LIVE` (2 minutes, runner/loop.py `live_run`). On Ctrl-C the runner leaves its busy session unclosed on purpose, so the next start recovers the interrupted job (`run_projects`, ADR 30 session D). That also leaves the run's row with no `ended`, so it looks live until the heartbeat ages out.

Proposed: on KeyboardInterrupt, mark the run's row ended (or clear its heartbeat) before re-raising, and keep the job's own state as it is for recovery. A restart then works at once. A run killed outright (kill -9, a crash) keeps the 2-minute rule. Maybe also say on refusal how long is left: "a run was live until 09:31:45; try again in 28 s".

## Plan (lead, 2026-10-29)

What was found in the code: the fix the note proposes exists already. Since f2-03, `runner/cli.py` `main` ends every run the command left open in its `finally` (`loop.end_open_runs`), so `runner run --here` never had this wait. `softfield run` (ADR 30 item 6) returns `_run_projects` before that `try:`, so it skips it. Only a Ctrl-C mid-job is hit: at an idle Ctrl-C `run_projects` closes its sessions itself. The metrics database holds 16 runs since 2026-10-15 left with no end, the three live ones aside.

### Decisions
- **D1.** `softfield run` goes through the same exit as every other command: its open runs end on any exit, the busy one with the verdict `interrupted` and no report, as `--here` does today. Nothing new in `run_projects`.
- **D2.** Recovery doesn't change: it reads `in_flight` from state.json, not the run's row, and `end_interrupted` still closes the cut-off job at the next start.
- **D3.** A run that still looks live (kill -9, a crash, a second terminal) keeps the 2-minute rule, and the refusal says when it was last seen and how long is left. `live_run` keeps its signature.

### Tickets
- `f138-01-ctrl-c-ends-the-run` (lead): D1–D3, one ticket.
