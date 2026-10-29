# Milestone F138: Run again right after Ctrl-C, without the 2-minute refusal

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-15.

## Notes
From the terminal session of 2026-10-15.

After Ctrl-C on `softfield run`, running it again says "runner: a run is live already (softfield): one runner at a time" for up to 2 minutes. The owner thought the runner was stuck.

Why: `softfield run` refuses while any project's run has a heartbeat under `LIVE` (2 minutes, runner/loop.py `live_run`). On Ctrl-C the runner leaves its busy session unclosed on purpose, so the next start recovers the interrupted job (`run_projects`, ADR 30 session D). That also leaves the run's row with no `ended`, so it looks live until the heartbeat ages out.

Proposed: on KeyboardInterrupt, mark the run's row ended (or clear its heartbeat) before re-raising, and keep the job's own state as it is for recovery. A restart then works at once. A run killed outright (kill -9, a crash) keeps the 2-minute rule. Maybe also say on refusal how long is left: "a run was live until 09:31:45; try again in 28 s".
