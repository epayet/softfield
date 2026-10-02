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

### M4 (2026-09-30): the first ADR 07 milestone ([review](../reviews/m4.md))

- **Q1:**
  - 7 headless escalations. Headless handling was worth it for m4-06's split and m4-07's requeue, since both unblocked dependants overnight.
  - 3 of the 7 existed only because of lead or runner mistakes: a protected test path, a pre-flight bug, and a stale runner process.
- **Q2:** the review ran interactively, at the owner's request. It found 1 blocking and 8 should-fix issues, all invisible to the gates, which an automated review would probably also have caught.
- **Q3:**
  - first-attempt pass 5/9, on specs with no pasted code, self-written tests and a new framework (Preact)
  - diffs of 180–500 lines passed when the ticket was one concept
  - m4-06 (4 dependencies, i18n, offline) failed until it was split, and the 30-minute timeout did most of the damage
- **Q4:** the French is correct but plain. One M3 finding recurred (m3-F5).
- **Q5:**
  - ≈18M Claude token-equivalents for the milestone: ≈2M per junior task, against M3's ≈1.8M
  - ≈10M of it was one lead session kept open during the runs
  - no usage-limit pause
- **Q6:** the generic runner changes were no-changes, pre-flight accepting unwritten tests, restarting after a runner change, and the timeout. Nothing Coucou-specific.
- **Anything else:** reading the junior's thinking (OpenCode's `opencode.db`) explains failures the gate logs can't. Peak junior context went from ~7% (M1–M3) to 26–43%.
- **Decisions affected:** ADR 07's keep-and-extend rule wasn't met, so tighten, per ADR 07: [ADR 12](12-junior-feedback-and-checkpoints.md). Dashboard: [ADR 13](13-factory-dashboard.md).
- **Owner's direction at sign-off:** steer mid-milestone rather than limit the plan: a checkpoint every 2 merges, lead direction before a ticket's last attempt, limits per trigger instead of a milestone cap, and one command (`runner milestone N`) that runs everything unattended. The owner prefers runs that need no oversight over the cheapest possible session pattern ([ADR 12](12-junior-feedback-and-checkpoints.md), Accepted).

### F1 (2026-10-02): the factory measures itself ([review](../reviews/f1.md), [factory review](../reviews/factory-f1.md))

- **Q1:** 7 escalations, 6 directions, 3 parks at a limit. Headless handling carried a 36-hour run with two owner sessions; build-on and `finish` (ADR 15) stopped retries throwing away nearly-right work.
- **Q3:** local Qwen 12/19 first-attempt at difficulty 2–6; Sonnet 3/3 as a developer; Opus merged all 28 lead tickets (14.8k lines, $4.65 per 1,000).
- **Q5:** ≈$84 of headless Claude, 82% on lead tickets. The week never passed 20%; the 5-hour window stopped the run four times (≈11 h of waiting).
- **Anything else:** reviewing costs about a tenth of writing (a checkpoint ≈$0.50 per 1,000 lines read); a different model's review found a bug the checkpoint missed. Replans cost 7% of lead spend and caught a gate blind spot and three wrong facts.
- **Decisions affected:** [ADR 16](16-claude-window-and-named-milestones.md) (Proposed): Claude's shared 5-hour window, the exact model per job, named milestones, standard replans. The extraction (this ADR) gains a concrete shape from the owner: `factory init` for any project (`docs/roadmap.md`).

### F2 (2026-10-02): cloud first ([review](../reviews/f2.md))

- **Q1:** 4 escalations, 1 direction, 1 checkpoint over 9 runs in ≈9 h. One escalation was spent only because a requeue wrote bare paths into a ticket: the third time, so it needs a check, not a rule.
- **Q3:** Opus merged all 9 lead tickets first time. Developers: 1 of 3 first time. gpt-oss-120b passed f2-13 in 9 min, but the gates passing didn't mean the Done when was met (3 of its 5 items weren't). nemotron-3-super blocked twice on f2-07.
- **Q5:** $32.11 of Claude, net savings from delegating −$1.08. Two waits for Claude's 5-hour window took ≈5.2 h of the ≈9 h, with nothing else to run: 9 of 11 tickets were the lead's.
- **Anything else:** a lead-only milestone is bound by the 5-hour window whatever the routing does. Cloud developers fail fast (minutes, not GPU half-hours), which makes a failure cheap but not useful.
- **Decisions affected:** none yet. If the next milestone with developer work shows the same gap between passing the gates and meeting the Done when, an ADR should give checkpoints the last merges before the review.

## 10. For the owner to decide at review time (each item can be accepted on its own)

1. 4.1: queue mode by default, and park the automated review loop.
2. 4.2 and 4.3: a separate factory repo, configured per project by `factory.toml`.
3. 4.4: FRONTIER.md plus pointer files.
4. 4.5: one report per milestone.
5. Whether to extract at all (Q7), and if so, when.
