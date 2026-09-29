# How the frontier + local workflow works

A plain-language overview. The rules are in [`workflow.md`](workflow.md) and [`task-format.md`](task-format.md), and the craft of writing tasks is in [`task-writing.md`](task-writing.md).

**The idea** ([ADR 07](adr/07-spend-less-frontier.md)): the frontier model is the tech lead and the local models are junior engineers. The lead designs, decides how the pieces connect, writes short tickets and builds the security-critical parts. The juniors write the rest, tests included. Deterministic gates check every change, and the lead reviews once per milestone. Until M3 the lead also wrote a working solution for every task, which cost more than doing the task; that's gone.

## The queue

It's just folders of Markdown task files, with no database or server:

```
tasks/ready/      waiting to run
tasks/done/       merged, with a result footer the runner appends
tasks/escalated/  the local model failed 3 times, or pre-flight failed; waiting for the frontier
```

`uv run runner run` loops over it:

1. **Pick** the lowest id in `ready/` whose `depends_on` tasks are all in `done/`.
2. **Branch** `task/<id>` from main.
3. **Pre-flight.** Every file path in backticks in the spec must exist (or be one the task creates), and every quoted `class`/`def` must be found in those files. If not, the task escalates straight away without spending model time.
4. **Local model.** A one-token warm-up request makes LM Studio load Qwen with the owner's settings. Then OpenCode runs with a short prompt: the rules, the task, and the commands to finish with.
5. **Gates**, stopping at the first failure:
   - no protected paths touched (including the tests that guard security code)
   - no test skipped or xfailed
   - no new dependencies
   - diff under a 1000-line backstop
   - test layout
   - translations
   - ruff
   - mypy
   - the task's own tests
   - the whole suite, minus other queued tasks' tests
   - the tests the task added or changed fail against main's code, so they really test the change
6. **Pass:** squash-merge into main and move the spec to `done/`. **Fail:**
   - attempt 2 continues on the same branch, with a one-line hint and the gate output at the end of the prompt;
   - attempt 3 starts from a fresh branch;
   - after 3 failures, the spec moves to `escalated/`.
7. **Escalation:** the headless frontier model, capped per milestone. It repairs or splits the spec, adds missing facts, does the task itself, or drafts an ADR for the owner. The runner commits its changes and moves the file.
8. **Session report:** written to `docs/sessions/` at the end.

After a milestone's tasks are done, `uv run runner review --milestone N` runs the staging end-to-end tests and a headless review. Blocking and should-fix findings become fix tasks or direct fixes, and nits go to the backlog. The loop stops on the rules in `workflow.md`.

Everything is plain git and files, so a bad run is easy to inspect (logs go in `var/runs/`) or undo.

## What goes in a ticket

A goal, the files to read, the worked example to follow, and acceptance criteria as bullets, including the edges. No pasted code and no working solution: the junior reads the code and writes the tests itself. Security work is the exception: the lead writes those tests first, on main. Details: [`task-format.md`](task-format.md).

What the juniors learn stays in the repo, since they have no memory: a check where possible, else a worked example, else one line in [`docs/agents/junior.md`](agents/junior.md) (15 lines at most).

## Results so far

M1 proper: 3 tasks, all passed on the first attempt, each taking about a minute of local model time and a few seconds of gates, with no frontier usage. The two calibration failures before that were spec errors, fixed by [ADR 01](adr/01-calibration-fixes.md). See `docs/reviews/m1.md`.
