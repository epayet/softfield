# Workflow: how Coucou gets built

> Reflects the brief §7 and [ADR 00](adr/00-initial.md) (Accepted). Changes to anything here need an Accepted ADR (see CLAUDE.md).

## Roles

| Who | Does |
|---|---|
| **Owner** | Accepts ADRs and workflow changes; signs off milestones on real devices. |
| **Claude** (Claude Code, Pro login) | Architect, planner and task-writer; sole implementer of protected paths; escalations; reviews. |
| **Runner** (`uv run runner`) | A deterministic Python script with **no AI in it**. It picks tasks, runs the local model and the gates, merges, retries and escalates, and calls Claude headlessly. |
| **Local model** (OpenCode + Qwen via LM Studio) | Implements one small task at a time. |

All coordination goes through files in the repo. Run logs go to `var/runs/<timestamp>-<task>/`, which is gitignored.

## Per-task loop

1. Pick the next `tasks/ready/*.md` whose `depends_on` are all in `done/`.
2. Create the branch `task/<id>` from `main`.
3. **Pre-flight:** every file in the task's Context and `Pattern to follow` exists, and every quoted symbol is found (`def`/`class` grep). If not, escalate at once.
4. **Local model:**
   - Warm up LM Studio with one sequential request, which JIT-loads it with the owner's settings. Warn if `loaded_context_length` ≠ `limit.context` in `opencode.json`.
   - Run `opencode run --title <id> -f <task> "<fixed instruction>"`, with a wall-clock timeout.
5. **Gates, in order, stopping at the first failure:**
   1. `BLOCKED.md` present → see below
   2. only `files:` changed (plus `docs/discoveries.md`)
   3. no protected path touched (`workflow/protected-paths.txt`)
   4. existing test files unchanged (SHA-256 against main)
   5. no dependency changes (`pyproject.toml` deps, `uv.lock`, `vendor/`)
   6. diff ≤ `max_diff` added + removed lines
   7. `layout`: unit test files match modules by name, one per module
   8. `ruff check` + `ruff format --check`
   9. `mypy`
   10. the task's `tests:`
   11. all unit + integration tests
6. **Pass:** squash-merge to `main` and `git mv` the task to `done/` with a result footer.
7. **Fail:**
   - attempt 2: same branch; the prompt adds the exact gate output
   - attempt 3: reset the branch; fresh prompt plus "previous attempt failed because…"
   - still failing: move the task to `escalated/` with logs and the last diff, pause its dependants, continue with independent tasks
8. **`BLOCKED.md`** (categories in AGENTS.md):
   - `unrelated-problem`: append it to `docs/discoveries.md` and continue gating
   - anything else: escalate immediately; this doesn't count as a failed attempt
9. **Discoveries:** the local model may append to `docs/discoveries.md`. Claude triages it at milestone review into the backlog, tasks or ADRs.

## Escalation (headless Claude)

- **When:** at most once per escalated task per runner pass, within the milestone cap.
- **What Claude gets:** the task, `BLOCKED.md` or the gate logs, and the last diff. Tools are limited to Read/Edit/Write on `tasks/`, `docs/` and the task's files, plus `uv run pytest`.
- **Outcome:** a repaired or split spec back in `ready/`, an answered question (facts added to Context), Claude doing the task itself, or **stop for the owner** (a draft ADR).

## Milestone review loop

**Trigger:** every task in the milestone is `done/` **and** `pytest -m e2e` passes on staging.

1. **Review round:** headless Claude reviews `git diff <milestone-base>..main` and writes the findings to `var/runs/review-mN-rK.json`.
   - **Blocking:** bugs, security issues, AGENTS.md or ADR violations.
   - **Should-fix:** design drift, missing edge cases, weak tests.
   - **Nit** → `docs/backlog.md`. Nits never loop.
2. **Routing each blocking or should-fix finding:**
   - small and clear → a fix task (`finding: mN-F3`)
   - protected, or quicker to fix than to specify → Claude fixes it directly
   - needs a design decision → a draft ADR, and **stop**
3. **Re-review:** covers only the fix diffs and whether each finding is resolved. New blocking issues in the fixes count; should-fix points about untouched code go to the backlog.

**Stop rules** (the values are in `workflow/runner.toml`):

| Rule | Default |
|---|---|
| Review rounds per milestone | 3 |
| Headless Claude runs per milestone (reviews + escalations) | 10 |
| A finding recurs a 2nd time | Claude fixes it (not the local model) |
| A finding recurs a 3rd time | stop |
| This round's findings ≥ the previous round's | stop |
| ADR needed / unresolved security finding / cross-milestone surprise | stop immediately |

**Report:** `docs/reviews/mN.md` covers what was built, the findings and their resolutions, the backlog items, the metrics (tasks, attempts per task, escalation rate, review rounds, headless runs), the stop reason and workflow observations. **Only the owner marks a milestone done.**

## Headless Claude invocation

- The environment has `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` **removed**, so the Pro login is always used.
- Flags: `claude -p --output-format json --permission-mode dontAsk --allowedTools <per job>`, with a wall-clock timeout (this CLI version has no turn cap).
- **Usage limit reached:** parse the reset time, record `paused_until` in `var/runs/state.json`, sleep and resume. Fallback backoff runs from 15 min up to 5 h. The runner never loops tightly.

## Improving the workflow

Evidence from milestone reports leads to an ADR, and nothing changes until the owner accepts it. Runner bug fixes that don't change behaviour are exempt.

## Session reports

The owner wants to learn how the frontier + local workflow performs, so every runner session leaves a report.

- **Deterministic part:** the runner writes `docs/sessions/YYYY-MM-DD-HHMM.md` at the end of each session, with no AI involved and no Pro usage. It covers:
  - tasks attempted, their outcomes and attempts, and wall-clock time per task and phase (warm-up, model, gates)
  - gate failures by gate, plus BLOCKED and escalation events
  - **local tokens:** input and output tokens processed by the local model, from OpenCode's JSON events
  - **headless Claude:** run count and token usage, from `claude -p --output-format json`
  - **frontier-savings estimate:** local tokens priced at Claude API list prices from `workflow/runner.toml`. This is notional on a Pro plan; it's shown to compare the two sides, not as a bill.
- **Narrative part:** what went well, what didn't, improvement opportunities and interesting observations.
  - Claude writes it whenever Claude is in the loop: calibration, milestone reviews, escalations and interactive sessions.
  - An optional headless narrative at the end of a session (`narrative = true` in `runner.toml`) is **off by default**, because it costs Pro usage and counts toward the milestone cap.
- Milestone reports (`docs/reviews/mN.md`) summarise the session reports of that milestone.
