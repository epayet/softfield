# How the frontier + local workflow works

A plain-language overview. The rules are in [`workflow.md`](workflow.md) and [`task-format.md`](task-format.md), and the craft of writing tasks is in [`task-writing.md`](task-writing.md).

**The idea:** the frontier model does the thinking (design, tests, a working solution) and the local model does the typing and verification. For small tasks, the frontier's share is most of the thought but little of the tokens.

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
3. **Pre-flight.** Every file path in backticks in the spec must exist, and every quoted `class`/`def` must be found in those files. If not, the task escalates straight away without spending model time.
4. **Local model.** A one-token warm-up request makes LM Studio load Qwen with the owner's settings. Then OpenCode runs with a short prompt: the rules, the task, and the commands to finish with.
5. **Gates**, stopping at the first failure:
   - only the task's `files:` changed
   - no protected paths touched
   - existing tests untouched
   - no new dependencies
   - diff within `max_diff`
   - test layout
   - translations
   - ruff
   - mypy
   - the task's own tests
   - the whole suite, minus other queued tasks' tests
6. **Pass:** squash-merge into main and move the spec to `done/`. **Fail:**
   - attempt 2 continues on the same branch, with the gate output at the end of the prompt;
   - attempt 3 starts from a fresh branch;
   - after 3 failures, the spec moves to `escalated/`.
7. **Escalation:** the headless frontier model, capped per milestone. It repairs or splits the spec, adds missing facts, does the task itself, or drafts an ADR for the owner. The runner commits its changes and moves the file.
8. **Session report:** written to `docs/sessions/` at the end.

After a milestone's tasks are done, `uv run runner review --milestone N` runs the staging end-to-end tests and a headless review. Blocking and should-fix findings become fix tasks or direct fixes, and nits go to the backlog. The loop stops on the rules in `workflow.md`.

Everything is plain git and files, so a bad run is easy to inspect (logs go in `var/runs/`) or undo.

## Before a task reaches the queue: the skeleton

The frontier model commits these to main first:

- **Stubs:** the exact function or method with its final signature and docstring, and `raise NotImplementedError` as the body. The local model fills in a shape; it doesn't design one.
- **Failing tests** that define done, one test file per task. They check behaviour, not implementation.
- **A throwaway reference implementation.** The frontier writes the task itself, runs the tests, ruff and mypy, then reverts. This proves the tests can pass (it caught an impossible query-count limit in M1) and gives the real diff size.
- **Spec checks:** `ruff format --check` and a runner dry-run, which includes pre-flight.

## What goes in a spec

The local model must never need to explore, and it drops instructions from long prompts. So specs are complete but short: Context of about 60 lines at most, 5 steps at most.

- **Goal:** one sentence.
- **Context:**
  - the current code it will edit, pasted verbatim;
  - facts it would otherwise look up, such as a `related_name`;
  - the one constraint that matters, in **bold** and also enforced by a test (e.g. "never show key or pairing fields").
- **Pattern to follow:** one existing file to copy the style from.
- **Steps:** close to dictation. The exact imports, the exact expression to return, and the trap to avoid.
- **Done when:** the same three lines every time.

## Results so far

M1 proper: 3 tasks, all passed on the first attempt, each taking about a minute of local model time and a few seconds of gates, with no frontier usage. The two calibration failures before that were spec errors, fixed by [ADR 01](adr/01-calibration-fixes.md). See `docs/reviews/m1.md`.
