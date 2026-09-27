# ADR 01: Workflow fixes from the calibration run

- **Status:** Proposed
- **Date:** 2026-09-27
- **Deciders:** project owner (accepts), Claude (drafts)
- **Evidence:** calibration run, 2026-09-27: `docs/sessions/2026-09-27-2344.md` and `docs/sessions/2026-09-27-2351.md`

## Context

The calibration ran two small M1 tasks through the whole pipeline. The local model's code was right every time, but the process lost **3 wasted model attempts and 2 headless Claude runs**. Every loss came from the workflow or from my specs, not from the model. Three of the causes are rules that only an Accepted ADR can change. Each item below is independent, so you can accept some and reject others.

## Decisions (proposed)

### 1. ⚑ `all-tests` ignores other queued tasks' skeleton tests

**Problem.** Skeleton-first puts failing tests on `main` for every queued task, and gate 12 requires the *whole* suite to pass. With two tasks in `ready/`, each one fails on the other's tests, forever. Calibration dodged this by queuing one task at a time. M1 proper, written as one batch, would stall.

**Change.** Gate 12 deselects the `tests:` files of the *other* tasks in `tasks/ready/` and `tasks/escalated/`. Everything else still runs, including the task's own tests (gate 11). When two queued tasks share a test file, I give them `depends_on` so they run in order.

### 2. ⚑ The ruff gate only checks Python files

**Problem.** `ruff format --check .` also formats the ```python blocks inside Markdown, including `tasks/ready/*.md`. m1-01's Context had one blank line between two pasted defs. The model's code passed every other gate, but ruff failed 3 times on a file the model isn't allowed to touch. That cost 3.7 min of model time plus one escalation.

**Change.** Add `extend-exclude = ["*.md"]` next to the existing migrations exclude in `pyproject.toml`'s `[tool.ruff]`, so ruff never gates on docs or task specs. (Snippets in specs should still be tidy, but a formatting slip in prose must not block code.)

### 3. ⚑ The local model's instruction mentions mypy and "not your file → BLOCKED"

**Problem.** The fixed prompt (`runner/prompts.py`, `LOCAL`) tells the model to run pytest and ruff, but not mypy. The model never ran mypy in 5 attempts, even when the task's Steps asked it to. And when the ruff gate failed on the task file, the retry read "IMPORTANT: … fix exactly that", ran ruff on its own files, and replied "all gates pass". It should have written `BLOCKED.md` (`needs-file`) and let Claude fix the spec at once.

**Change.** Add two lines to `LOCAL`:
- "Then run `uv run mypy coucou`." (after the ruff line)
- "If a gate fails on a file that isn't in `files:`, you can't fix it: write BLOCKED.md with `CATEGORY: needs-file` naming that file, and stop."

## Consequences

- M1 can be queued as one batch and run unattended (item 1).
- Spec formatting slips no longer cost model attempts (item 2), and spec errors that do slip through reach Claude after 1 attempt instead of 3 (item 3).
- Item 1 loosens checking slightly: a task could break a queued task's tests unnoticed until that task runs. Its own `task-tests` gate would then fail with the cause visible in the logs.
- The size is roughly 15 lines of runner code plus runner tests, one config line and a sentence in `docs/workflow.md`.

## Alternatives considered

- **Keep queuing one task at a time** (item 1). This needs no change, but Claude has to feed the queue after every merge.
- **`xfail(strict=True)` on skeleton tests** (item 1). Rejected: the model would have to edit an existing test file, which AGENTS.md forbids.
- **Only rely on me formatting specs** (item 2). I now run `ruff format --check` on specs before committing them (it caught m1-02), but a gate shouldn't depend on my diligence.

## Not in this ADR (no rule change needed)

- The runner report now shows warm-up per task, and a requeued task gets its own log folder. Both were bug fixes, already committed.
- A `runner check-task <file>` command that runs pre-flight on a spec before I commit it. It adds a tool without changing any rule; I'll add it if you want it.
