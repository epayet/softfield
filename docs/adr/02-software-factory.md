# ADR 02: Extract the workflow into a reusable "software factory"

- **Status:** Draft, **work in progress**. Not for decision yet. Review after M3 or M4, whichever comes first with at least ~15 tasks of evidence.
- **Date:** 2026-09-28 (first draft)
- **Deciders:** project owner (accepts), Claude (drafts)
- **Evidence:** `docs/reviews/m1.md`, ADR 01, `docs/sessions/`

## Context

The owner wants to reuse the Coucou workflow on other projects. The local side stays OpenCode + Qwen via LM Studio (JIT, owner's settings as-is). The frontier should be pluggable: Claude Code today, possibly GitHub Copilot (free tier) or another tool later. The owner also asks whether the current workflow is too complex, and whether it reinvents existing tools.

This is a **work-in-progress** ADR. M1 alone is too little evidence to decide on, so §8 lists the questions the next milestones should answer, and §9 is a log that each milestone review adds to. Sections 1–7 are the current best guess and may change.

## 1. Is it too complex? Partly yes, and M1 shows where

| Part | M1 evidence | Verdict |
|---|---|---|
| Task format, skeleton-first, pre-flight, file-level gates, retry → escalate | 3/3 first-attempt passes after ADR 01; 3.3 min model time for 3 tasks | **Earns its keep.** This is the core. |
| Headless escalations | 2 runs, both on calibration spec errors; both could have waited for the next interactive session | Optional |
| Headless review loop (rounds, recurrence tracking, "findings ≥ last round" rule, review JSON, per-milestone cap, `runner/review.py`, most of `runner/milestone.py`) | 1 round, 1 finding, fixed by Claude directly. No stop rule fired. The owner reviews and signs off interactively anyway. | **Over-built for now** |
| Usage-limit pause / backoff, `paused_until` | Never triggered | Needed only if headless stays |
| Three reporting layers (session report, `mN-metrics.md`, `mN.md`) | `runner status` miscounted requeued attempts; the M1 metrics were corrected by hand | Merge into one |
| Headless narrative, API prices | The narrative is off by default. The prices are notional. | Keep the prices as information; drop the narrative |
| Docs: `workflow.md`, `how-it-works.md`, `task-format.md`, `task-writing.md`, AGENTS.md, CLAUDE.md | Overlap. Several rules are restated in 2–3 places. | Consolidate when extracting |

About half the runner exists to drive a frontier headlessly: `runner/claude.py`, `runner/review.py`, most of `runner/milestone.py`, the caps in `runner/state.py`, and the ESCALATION/REVIEW/NARRATIVE prompts in `runner/prompts.py`. That half is also what ties the runner to Claude. **So removing that complexity and making the frontier pluggable are the same change.**

## 2. Generic vs project-specific vs frontier-specific

| Generic (factory) | Project-specific (config and files in the repo) | Frontier-specific |
|---|---|---|
| `tasks.py` (format, picking, deps, pre-flight, footer) | Gate **commands**: ruff, mypy, pytest dirs, `check-i18n`, `check-layout` | `claude.py`: `claude -p`, stripped `ANTHROPIC_*` env, JSON usage, limit-text parsing |
| `gitops.py`, `state.py`, `report.py` | `workflow/protected-paths.txt` | Tool-allow syntax (`Bash(uv run pytest:*)`) |
| `local_model.py` (warm-up, `opencode run`, token parsing) | Dependency files and dirs (`pyproject.toml`, `uv.lock`, `vendor/`) | ESCALATION/REVIEW prompt wording ("Follow CLAUDE.md") |
| File-level gates: allowed files, protected, existing tests unchanged, deps, max_diff, BLOCKED | Layout rule (`tests/unit` ↔ `coucou/`), i18n gate (`runner/i18n.py`) | `CLAUDE.md` as the frontier's instruction file |
| LOCAL/RETRY/FRESH prompts, with the project's check commands filled in | AGENTS.md **code** rules (§Code, §What to read), task id prefix | The headless section of `docs/workflow.md`; the prices in `runner.toml` |
| Protocols: BLOCKED categories, discoveries, the `escalated/` queue, review grading | Test tiers, the e2e trigger command | `.github/copilot-instructions.md`, if Copilot is used |

## 3. What the frontier actually has to do

- **Interactive, with the owner:** milestone planning, ADRs, skeletons and failing tests, reference implementations, protected-path code, reviews, the French check, and reports. This is almost all of the frontier's value. **Any capable agentic coding tool can do it**: it has to read, edit, run shell commands and follow an instructions file.
- **Headless, inside the runner:** escalations and review rounds. Both can wait. An escalated task already sits in `tasks/escalated/` with its logs and last diff, the runner already carries on with independent tasks, and `--no-escalate` already exists.

**So a frontier with no headless mode, or with a tight quota, still works.** Escalations queue up and are handled at the start of the next interactive session (a small `factory inbox` command would list them with their log paths). Reviews happen interactively at the end of the milestone. The cost is latency: tasks that depend on an escalated task wait for the owner. That's acceptable at this scale; in M1 all escalations were early spec errors.

**GitHub Copilot: facts to verify before deciding.** Web access failed while drafting. These come from memory, as of mid-2025, and are **unverified**:
- **Copilot Free:** about 2,000 completions and about 50 chat/premium requests per month. Agent-mode prompts count against the 50, multiplied by the model's multiplier.
- **Copilot CLI (`copilot`):** has a programmatic mode, `-p "<prompt>"`, with `--allow-tool`, `--deny-tool` and `--allow-all-tools`.
  - At launch it needed a **paid** plan (Pro, Pro+, Business or Enterprise), so the free tier may have no CLI at all.
  - Whether it can output usage as JSON is unconfirmed.
- **Instruction files:** Copilot reads `AGENTS.md` and `.github/copilot-instructions.md`.
- **Implication if confirmed:** Copilot Free could be an *interactive* frontier (agent mode in VS Code) at about 50 prompts a month. Queue mode would then be required, and a whole milestone would have to fit in about 50 prompts. Headless Copilot would need Copilot Pro.

## 3b. Prior art: what exists already, and what is specific to this setup

These are from memory and **unverified**; check them before deciding (Q7).

- **Frontier plans, cheaper model edits:** Aider's architect/editor mode.
- **Spec → plan → task files, tool-neutral:** GitHub Spec Kit, Taskmaster AI, Kiro specs, the BMAD method.
- **Loop an agent until the checks pass:** the "Ralph" loop, OpenHands and SWE-agent harnesses, CI and pre-commit gates.

None of these combines the parts that are **specific to this setup**:

1. **A local executor.** It runs on consumer hardware (LM Studio JIT, owner's settings as-is), and task sizing is tuned to its weaknesses: short prompts, key instruction last.
2. **Hard gates, not trust.** A deterministic runner with no AI in it enforces them: only allowed files change, protected paths are untouched, existing tests are immutable, dependencies don't change, and the diff stays under max_diff.
3. **Skeleton-first.** The frontier writes the stubs, the failing tests and a throwaway reference implementation, so the local model only fills in shapes.
4. **A structured BLOCKED/escalation protocol** instead of interactive questions.
5. **A rationed frontier.** It runs on a subscription quota (Pro, maybe Copilot Free), not API billing.
6. **Measured learning.** Session reports and milestone metrics feed ADRs.

**Implication:** the specs → tasks half could reuse Spec Kit or Taskmaster conventions instead of inventing new ones. The factory's own value is the enforcement half: items 1–4 and 6. Before building, spend about 30 minutes checking whether Spec Kit's task files could feed the runner directly.

## 4. Decisions (current best guess, not yet proposed)

### 4.1 ⚑ Headless frontier becomes optional; queue mode is the default

- The runner never calls a frontier unless `[frontier] headless = true`.
- By default, escalated tasks wait in `tasks/escalated/`. The milestone review is interactive: the frontier and the owner do it together, with the same grading and routing rules (`docs/workflow.md` §Milestone review loop).
- **Park the automated review loop.** `review.py` and the round and recurrence stop rules leave the core. They stay in git history, and an ADR can bring them back if a milestone needs them.
- The cap of 10 headless runs per milestone applies only when headless is on.

### 4.2 One extracted package; a "frontier" is just a command template

- A new repo, `~/projects/epayet/factory`, holds a package `factory` (renamed from `runner`, with a `factory` CLI), installed with `uv tool install -e`.
- There is no adapter class hierarchy. Headless, when it's on, is configured like this:
  ```toml
  [frontier]
  headless = false
  name = "claude"          # preset: command + env stripping + JSON usage parsing
  # or, for any other tool:
  # command = ["copilot", "-p", "{prompt}", "--allow-all-tools"]
  ```
- There is one function, `run_frontier(prompt, tools) -> Result(ok, text, usage | None)`.
  - The `claude` preset keeps today's env stripping, JSON usage and limit parsing.
  - A generic command gets plain text, no usage numbers, and backoff-only handling of usage limits.
- A real adapter interface earns its keep only once a second frontier is used headlessly, and none is today.

### 4.3 A per-project `factory.toml` replaces `workflow/runner.toml`

```toml
[project]
name = "coucou"
src = ["coucou"]
dependency_files = ["pyproject.toml", "uv.lock"]
dependency_dirs = ["coucou/static/coucou/vendor/"]
protected = "workflow/protected-paths.txt"

[[gates]]            # after the generic file-level gates, in order
name = "layout"
cmd = ["uv", "run", "factory", "check-layout", "tests/unit:coucou"]
[[gates]]
name = "translations"
cmd = ["uv", "run", "python", "-m", "coucou_checks.i18n"]
[[gates]]
name = "ruff"
cmd = ["sh", "-c", "uv run ruff check . && uv run ruff format --check ."]
[[gates]]
name = "mypy"
cmd = ["uv", "run", "mypy", "coucou", "tests"]
# task-tests and all-tests stay built in: they need the task's tests: list and the ADR 01 deselect

[tests]
cmd = ["uv", "run", "pytest", "-q"]
suite = ["tests/unit", "tests/integration"]

[local_model]  # unchanged: base_url, model, opencode_model; LM Studio settings as-is
[caps]         # unchanged values
```

- The i18n gate is Coucou-specific. It moves into the Coucou repo as a command that the gate calls.
- The layout gate stays generic, with the directory pairs taken from config.
- The local model's "Finish by running …" line is built from the same gate commands, so they are defined in one place.

### 4.4 ⚑ Tool-neutral instructions

- `AGENTS.md` stays the file **every** agent reads, and it stays **short**.
  - OpenCode loads it into every local prompt, and Qwen drops instructions from long prompts (ADR 01).
  - So the frontier's duties do **not** go in AGENTS.md.
- The frontier's duties move to a tool-neutral **`FRONTIER.md`** that names no vendor. They are today's CLAUDE.md body: authority, skeleton-first, protected paths, escalations, review and ADRs.
- `CLAUDE.md` becomes a two-line pointer (`@AGENTS.md`, `@FRONTIER.md`). `.github/copilot-instructions.md` would be the same, if Copilot is used.
- The generic parts of `docs/workflow.md`, `task-format.md` and `task-writing.md` move to the factory repo's `docs/`.
  - Coucou keeps only its own additions (French, layout, the protected list) in one `docs/workflow.md`.
  - `how-it-works.md` merges into that file.

### 4.5 One report per milestone

- The deterministic session reports stay.
- `mN-metrics.md` goes. `mN.md` takes its metrics from `factory status`, fixed to count attempts across requeues, so nothing needs correcting by hand.

## 5. Migration and validation (when the decision is made)

- **Timing:** extract only **between milestones**, never while a Coucou runner is running.
- **Steps:**
  1. Create the factory repo from `runner/` and `tests/runner/`, keeping history with `git subtree split`.
  2. Apply 4.1–4.3 there, with its tests green.
  3. In Coucou, remove `runner/`, add `factory.toml`, `FRONTIER.md` and the pointer files, and update `protected-paths.txt`.
- **Replay check:**
  - `factory run --dry-run` in Coucou lists the same queue as `runner run --dry-run`.
  - Re-running the gates on M1's merged tasks (check out each pre-merge commit) gives the same verdicts.
- **Live check:** the next Coucou milestone after the extraction runs through `factory` in queue mode. Success means:
  - the first-attempt pass rate is no worse than the trend since ADR 01;
  - escalations are handled in the next interactive session with no lost context;
  - the milestone report needs no hand-corrected metrics.
- **Genericity check:** set up one small repo that isn't Django (e.g. a CLI tool) with `factory.toml`, AGENTS.md and FRONTIER.md, and run 2–3 tasks through it. If the factory's code has to change for it, the generic/project split was wrong; record that in the milestone report.
- **Frontier check (optional, after the Copilot facts are verified):** run one interactive planning and skeleton session with Copilot using FRONTIER.md, and note what it misses compared with Claude.

## 6. Consequences

- The runner loses about half its code (the headless review loop, the caps, the narrative). The workflow docs shrink to one generic set plus a short page per project.
- In queue mode, escalations take longer to resolve, because dependent tasks wait for the next interactive session.
- Automated multi-round review is gone until an ADR brings it back. Reviews depend on the owner holding an interactive session at the end of each milestone, which already happens for sign-off.
- There is a second repo to maintain. It is installed editable, so a fix there reaches every project at once.

## 7. Alternatives considered

- **Keep everything and add a `Frontier` Protocol with Claude and Copilot adapters.** This keeps all the complexity to support a headless Copilot that may not exist on the free tier.
- **Copy the runner into each project.** Simplest to start, but fixes drift between the copies.
- **Put the frontier's duties in AGENTS.md.** One file instead of two, but it bloats every local-model prompt (ADR 01).
- **Adopt an existing tool (§3b) for the front half.** Still open (Q7).

## 8. Why wait: questions the next milestones should answer

M1 is thin evidence: 5 tasks, near-dictation specs, no French yet, and no usage limit hit. Each answer below could change a decision above.

| # | Question | Could change |
|---|---|---|
| Q1 | Did any escalation *need* headless handling, or could it have waited for the next interactive session? What would waiting have cost (tasks paused, hours)? | 4.1 queue mode |
| Q2 | Did the automated review loop ever run more than one round, or catch anything an interactive review wouldn't have? | 4.1 parking the review loop |
| Q3 | What is the pass rate on less-dictated specs, and on larger tasks (≤ ~80 lines)? | how generic the task-writing guidance is; which docs move |
| Q4 | How good is the local model's French (the M2 pairing UI)? | whether i18n is a gate or a review item |
| Q5 | How much frontier use does a milestone take (interactive sessions, headless runs, limit pauses)? | whether a quota of ~50 requests a month could ever fit |
| Q6 | Which runner changes were Coucou-specific, and which generic? | the split in §2 |
| Q7 | Prior art (§3b), once checked: could Spec Kit or Taskmaster task files feed the runner? Does something existing already cover the enforcement half? | whether to extract at all, or adopt an existing tool |
| Q8 | Copilot facts (§3), once verified | the frontier options |

## 9. Learnings log (one entry per milestone review)

<!-- Template:
### M<n> (YYYY-MM-DD)
- Q1–Q8: answers with evidence (link docs/reviews/mN.md, docs/sessions/…)
- Anything else that bears on the factory
- Does this change a decision above? Which, and how?
-->

### M1 (2026-09-28): baseline

- **Q1:** 2 headless escalations, both calibration spec errors; both could have waited.
- **Q2:** 1 round with 1 should-fix, fixed directly; no stop rule fired.
- **Q3:** 3/3 first-attempt passes on ~30–40-line diffs, with near-dictation specs.
- **Q5:** 3 of 10 headless runs used; no usage-limit pause.
- **Q4, Q6–Q8:** no evidence yet.

### M2

_(to fill in at the M2 review)_

### M3

_(to fill in at the M3 review)_

## 10. For the owner to decide at review time (each item can be accepted on its own)

1. 4.1: queue mode by default, and park the automated review loop.
2. 4.2 and 4.3: a separate factory repo, configured per project by `factory.toml`.
3. 4.4: FRONTIER.md plus pointer files.
4. 4.5: one report per milestone.
5. Whether to extract at all (Q7), and if so, when.
