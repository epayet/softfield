# ADR 02: Extract the workflow into a reusable "software factory"

- **Status:** Draft, **work in progress**. Not for decision yet. Review after M3 or M4, whichever comes first with at least ~15 tasks of evidence.
- **Date:** 2026-09-28 (first draft)
- **Deciders:** project owner (accepts), Claude (drafts)
- **Evidence:** `.factory/reviews/m1.md`, ADR 01, `.factory/sessions/`

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
| `gitops.py`, `state.py`, `report.py` | `.factory/protected-paths.txt` | Tool-allow syntax (`Bash(uv run pytest:*)`) |
| `local_model.py` (warm-up, `opencode run`, token parsing) | Dependency files and dirs (`pyproject.toml`, `uv.lock`, `vendor/`) | ESCALATION/REVIEW prompt wording ("Follow CLAUDE.md") |
| File-level gates: allowed files, protected, existing tests unchanged, deps, max_diff, BLOCKED | Layout rule (`tests/unit` ↔ `coucou/`), i18n gate (`runner/i18n.py`) | `CLAUDE.md` as the frontier's instruction file |
| LOCAL/RETRY/FRESH prompts, with the project's check commands filled in | AGENTS.md **code** rules (§Code, §What to read), task id prefix | The headless section of `docs/workflow.md`; the prices in `runner.toml` |
| Protocols: BLOCKED categories, discoveries, the `escalated/` queue, review grading | Test tiers, the e2e trigger command | `.github/copilot-instructions.md`, if Copilot is used |

## 3. What the frontier actually has to do

- **Interactive, with the owner:** milestone planning, ADRs, skeletons and failing tests, reference implementations, protected-path code, reviews, the French check, and reports. This is almost all of the frontier's value. **Any capable agentic coding tool can do it**: it has to read, edit, run shell commands and follow an instructions file.
- **Headless, inside the runner:** escalations and review rounds. Both can wait. An escalated task already sits in `.factory/tasks/escalated/` with its logs and last diff, the runner already carries on with independent tasks, and `--no-escalate` already exists.

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
- By default, escalated tasks wait in `.factory/tasks/escalated/`. The milestone review is interactive: the frontier and the owner do it together, with the same grading and routing rules (`docs/workflow.md` §Milestone review loop).
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

### 4.3 A per-project `factory.toml` replaces `.factory/project.toml`

```toml
[project]
name = "coucou"
src = ["coucou"]
dependency_files = ["pyproject.toml", "uv.lock"]
dependency_dirs = ["coucou/static/coucou/vendor/"]
protected = ".factory/protected-paths.txt"

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
- Q1–Q8: answers with evidence (link .factory/reviews/mN.md, .factory/sessions/…)
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

### F3 (2026-10-04): the factory line ([review](../reviews/f3.md))

- **Q1:** 11 escalations, 12 directions, 5 checkpoints for 25 merges. Most escalations were `finish` or `implemented` after Qwen read for 10 minutes without an edit; four were fix tickets whose `files:` held only tests, which no developer can pass (now a pre-flight check).
- **Q3:** Qwen 2 of 16 first time on the line's SVG and its fixes; Opus finished most of them. gpt-oss-120b 1 of 8: careless edits, failed in a minute.
- **Q5:** $48.46 of Claude; net savings from delegating −$15.43, the worst so far. Supporting a developer on an SVG ticket cost more than writing it.
- **Anything else:** the checkpoints caught real gaps (11 findings, all confirmed), but both their fix tickets and the checkpoint after them let a DOM XSS through. The all-tests gate skipped every test file a ready ticket listed, so the line's tests ran in no gate and a regression reached main.
- **Decisions affected:** [ADR 21](21-gate-every-test-file.md) (Proposed) drops ADR 01 item 1's skip. Drawing work (SVG layout, motion) goes to the lead or to small, picture-backed developer tickets on a lead-written core.

### F4 (2026-10-04): always on ([review](../reviews/f4-always-on.md))

- **Q1:** the lead tickets (01, 03, 05, 07, 09, 11, 15, 19, 20, 33) all merged first time with no escalation. The escalations went to fix tickets: three tests-only ones (f4-24, f4-26, f4-36) that no developer could pass, and two whose directions didn't save them (f4-28, f4-29).
- **Q3:** the runner's own numbers say 10 of 21 first time. The F4 dashboard tickets (02, 04, 06, 08, 10, 17, 18) were small and passed, but the checkpoints found weak or vacuous tests behind five of them (04, 06, 08, 10, 18), and fixing those took 12 fix tickets, some fixing the previous fix.
- **Q5:** $19.11 of Claude, net savings −$1.69: close to even, unlike F3.
- **Anything else:** 20 of the checkpoints' 21 findings were real, the Copilot stand-in's 11 included. The stand-in filed its fix tickets under the wrong milestone and with wrong paths, which f4-33 now fixes. A plan change in another milestone (f3-05 dropped the Queue table) silently undid an F4 outcome ("what waits for what"), and no checkpoint could see it.
- **Decisions affected:** none. The `later/` folder and `runner queue` (ADR 17 item 3) were used for real at once: f3-22's proposals wait there for the owner.

### F7 (2026-10-05): factory fixes ([review](../reviews/f7-factory-fixes.md))

- **Q1:** no escalation, direction or checkpoint. Six lead tickets merged first time in six short runs over ≈1.5 h, each ending with "the runner needs a fresh process".
- **Q3:** no developer work: every ticket was runner code (protected).
- **Anything else:** measure before you fix. f7-06's probe ran a real `opencode run` and found the cause in `PWD`, which two earlier fixes (f2-12's clone, f4-19's root commit) had guessed wrong. The same probe showed that every earlier OpenCode bench was invalid, and those benches feed ADR 24's recompute. So a ratings fix built on bench data has to check how that data was made. The review routed it to f7-07.
- **Decisions affected:** none. ADR 24 holds. Its expected ratings (Qwen ≈3, gpt-oss-120b ≈2) wait for f7-07's recompute without the void benches.

### F6 (2026-10-08): the planning room ([review](../reviews/f6-planning-room.md))

- **Q1:** 6 escalations, 8 directions, 5 checkpoints for 30 merges. The four page tickets of the first night (f6-07 to f6-10) were all `finish` or `implemented` by Opus after Qwen read for 10 minutes without an edit or timed out (445 min, 1 merge).
- **Q3:** Qwen 7 of 15 first time. It passed the small fix tickets (f6-25 to f6-28, f6-30) in one attempt each, and failed the page tickets that had to read new modules.
- **Q5:** $51.98 of Claude, net savings −$10.40. Supporting Qwen on the page tickets cost more than writing them.
- **Anything else:** the checkpoints found 7 real findings, all fixed by tickets before the review. The review found two more in the same Coming code: one helper read the running jobs without the "live" filter its two neighbours use, and two pages parsed a request's value strictly although `POST /requests` stores any value. The steering loop worked from the dashboard while paused, which was the owner's aim.
- **Decisions affected:** none. The lesson "split a page ticket to one template or one function on an existing pattern" is in lead.md's Known range.

### F20 (2026-10-08): data safety ([review](../reviews/f20-data-safety.md))

- **Q1:** two lead tickets on the runner, both first time, ≈1 h together; no escalation, direction or checkpoint. Planned on 2026-10-07 and built the next morning, from the owner's question to a backup in Dropbox in under a day.
- **Q3:** no developer work (protected runner code).
- **Q5:** $3.75 of Claude.
- **Anything else:** both features were already in real use before the review: a copy in `~/Dropbox/software-factory-backups` and five threads in `.factory/planning/`. Reading the real exports showed the lead's points twice in each reply (text and boxes), which is the planner prompt's doing and already F41's fix. The review found no code defect; it added the restore steps (a backup nobody knows how to restore is half a backup) and one test.
- **Decisions affected:** none.

### F41 (2026-10-08): the points carry everything ([review](../reviews/f41-i-find-that-on-conversations-there.md))

- **Q1:** two small tickets, both built by the lead in one terminal session with the owner; no escalation, direction or checkpoint. The runner's report reads "0 of 2 merged" because it only counts its own merges (backlog).
- **Q3:** no developer work: f41-02 was a developer ticket, but the lead built it with f41-01 in the same session.
- **Q5:** $1.13 of Claude.
- **Anything else:** the review found the one place the fold hid something the owner must see: F49's "the runner didn't apply this merge" note, appended to the lead's text the same day. Two milestones touching the same reply a few hours apart, with no checkpoint on either, is where such gaps slip through; reading the other writers of a field you change catches them.
- **Decisions affected:** none.

### F55 (2026-10-08): settled threads leave the desk ([review](../reviews/f55-dismiss-all-conversations-where-the-related.md))

- **Q1:** one lead ticket, built by the lead in a terminal session together with the settling half of f31-01 (F31 D1); no escalation, direction or checkpoint. The report reads "0 of 1 merged" for the same reason as F41.
- **Q3:** no developer work (protected runner code).
- **Q5:** $1.24 of Claude.
- **Anything else:** building F55 with F31 D1 in one commit was right: they share `proposal_state`, which now lives in `runner/planner.py` and serves the desk, the thread page and the runner alike, so "settled" has one meaning. The clear-out's tests covered only threads whose lead reply had no proposals; the review added the realistic case (a plan approved, an ADR left open).
- **Decisions affected:** none.

### F50 (2026-10-08): a finished card shows its review ([review](../reviews/f50-the-data-safety-review-it-asks.md))

- **Q1:** three developer tickets (difficulty 2–3, `factory_dashboard/` only), built instead by the lead in one terminal commit (`4b9fefe`); no escalation, direction or checkpoint. The report reads "0 of 3 merged" for the same reason as F41.
- **Q3:** no developer work, though all three were planned for one: a developer ticket the lead builds itself leaves no result for the Known range.
- **Q5:** $2.06 of Claude, this review included.
- **Anything else:** the Sign off button copied Archive's pattern, and Archive's pattern predates the owner's 2026-10-07 rule: a press showed "Asked" in grey, not the dashed "Signing off" that the Done when named. The proposal page's `on-its-way` class is the pattern that meets the rule; the review fixed Sign off with it. When copying a button, copy the newest one.
- **Decisions affected:** none.

### F8 (2026-10-09): one visible queue ([review](../reviews/f8-one-queue.md))

- **Q1:** 1 escalation (f8-06, implemented by Opus after 3 failed Qwen attempts), 2 directions, and the checkpoints after f8-07. 12 merged. All 8 lead tickets on the runner passed first time.
- **Q3:** Qwen 2 of 4 first time. It passed the fix tickets and failed the page tickets (see lead.md, Known range).
- **Q5:** $27.65 of Claude, net savings −$1.25.
- **Anything else:** the metrics hid the checkpoints' work. A checkpoint files its findings under the milestone of the merge that queued it, so the four findings on F8's tickets went under F9, and F8's report said "Findings: none". The review fixed it (each finding goes under the milestone of the ticket at fault). Until then, per-milestone checkpoint numbers before F8 may be off where a checkpoint's merges spanned milestones. The review also found a re-check filter, added in F8 itself, that silently dropped real findings: a guard that duplicates a prompt instruction can cost more than the duplicates it prevents.
- **Decisions affected:** none. ADR 22 holds as built.

### F26 (2026-10-10): numbers on the desk ([review](../reviews/f26-i-want-to-see-numbers-next.md))

- **Q1:** one developer ticket, first time, with no escalation, direction or checkpoint (it was the run's last merge, so only the review read it, as with f2-13).
- **Q3:** Qwen 1 of 1 at difficulty 2: two template lines on a worked example in the same file, 41 min.
- **Q5:** see the review's numbers; the ticket itself cost no Claude.
- **Anything else:** the card went from the owner's note (2026-10-07) to an approved plan the next morning, then waited two days at priority 6 behind F9's line work: for a two-line change, the queue was the whole delay. The plan's D2 said "four groups" and "the sum of their items"; by the time it was built the desk had five groups and left out cards on their way. Reusing the tab's number made the code right anyway, where a sum written from the plan would have been wrong: point a ticket at the value to reuse, not at a recipe to recompute.
- **Decisions affected:** none.

### F12 (2026-10-10): notifications asked once ([review](../reviews/f12-turn-on-notifications-little-feedback-button.md))

- **Q1:** two developer tickets, both first time; one checkpoint, whose two findings were real and became the second ticket. No direction, no escalation.
- **Q3:** Qwen 2 of 2 at difficulty 3–4 on one script with a worked example (a stand-in `Notification`), 59 and 36 min.
- **Q5:** see the review's numbers.
- **Anything else:** every gate and the checkpoint passed a feature that could not work on the owner's address, the one case the milestone exists for. The test made a state no browser has (not secure, permission "default"): Chrome answers "denied" there, so the steps never showed. The review found it by opening a real plain-http address in the test browser, which took three seconds. A stand-in for a browser API proves the code's logic, not the browser's behaviour: when a ticket is about what a browser does on some kind of address, its Done when must name one test with the real API. The review also left a scratch test file it could not delete; a headless job that needs a probe writes it inside an existing test file.
- **Decisions affected:** none. ADR 26 holds; "Got it" no longer counts as the answer to the question (ADR 26 item 2 says the steps show once, not that they replace the question).

### F31 (2026-10-12): proposals close the loop ([review](../reviews/f31-when-i-click-on-approve-plan.md))

- **Q1:** five tickets, one merged by the runner first time (a headless lead ticket), three built by the lead in a terminal with the owner, one done headless then landed by hand after two days behind the weekly reserve and a red main. No escalation, direction or checkpoint. A sixth ticket waits in `.factory/tasks/later/` for a mock-up.
- **Q3:** no developer work: four tickets are protected runner code, and the one developer ticket was built by the lead.
- **Q5:** see the review's numbers.
- **Anything else:** two findings of one kind. The milestone gave an existing thing a new meaning and one older reader or writer of it wasn't told: Reject settled a merge, but Approve plan still applied every merge of the thread; "the latest list of proposals" began to decide which buttons show and when a thread closes, but the planner prompt still asked for only the proposals changed this turn. When a ticket changes what a stored field means, its Context should name every reader and writer of that field, the prompts among them. The start tag was five days and 309 files old, so the review read the card's commits, not the milestone diff.
- **Decisions affected:** none.

### F48 (2026-10-13): Try again plants a note, once ([review](../reviews/f48-the-didnt-go-through-cards-try.md))

- **Q1:** two tickets, both first time: one by Qwen, one by a headless lead job whose branch was landed by hand after a red main. One checkpoint, no finding. No escalation or direction.
- **Q3:** Qwen 1 of 1 at difficulty 2 (a Jinja global and five templates, 35 min); its tests covered two of the ticket's five Done-when lines, and the checkpoint passed them.
- **Q5:** see the review's numbers.
- **Anything else:** about an hour of building took four days to land: two and a half waiting for the weekly reserve, then a red main. It is the third review running (F26, F12, F48) where the review, not the checkpoint, found the missing test: a checkpoint should be given the ticket's Done-when lines and asked for the test behind each.
- **Decisions affected:** none.

### F53 (2026-10-13): a review waiting for Claude doesn't stop the line ([review](../reviews/f53-why-is-milestone-diff-review-waiting.md))

- **Q1:** one ticket, a headless lead job on protected runner code, merged first time. No escalation, direction or checkpoint. The review filed one developer ticket.
- **Q3:** no developer work yet; the fix ticket is the first.
- **Q5:** see the review's numbers.
- **Anything else:** the last support job that slept instead of parking now parks: on 2026-10-08 that sleep cost 3 h 30 with about 40 tickets ready. Two findings of one kind, both from the ticket's wording. It said which tests to "replace", and one covered code that still runs under another command; the plan's Done when named two places (the console and the queue) and the ticket carried one. A ticket that replaces a test says whether the old behaviour is gone or moved, and a Done-when line that names two places is checked against both.
- **Decisions affected:** none. ADR 16 item 4 now holds for every support job; ADR 22's "a due review keeps its place" holds whenever Claude can take it.

### F79 (2026-10-13): a retry after a timeout names the branch's files ([review](../reviews/f79-when-a-task-times-out-on.md))

- **Q1:** one ticket, a headless lead job on protected runner code, merged first time in 24 minutes. No escalation, direction or checkpoint. The review fixed two small things itself and filed no ticket.
- **Q3:** no developer work.
- **Q5:** see the review's numbers.
- **Anything else:** the card was a question the owner planted; the answer from the code found one real gap, which became a 16-line ticket. The review's diff was 890 lines because a terminal session's commits for three other milestones sat between the merge and the review: a round-1 review should be pointed at its own merges when that happens (backlog, f79-F3). Whether the list saves retries isn't measured yet.
- **Decisions affected:** none. ADR 12 item 5's retry line gains one sentence; `docs/workflow.md` says so.

### F104 (2026-10-13): a mock-up answers in the review page's frame ([review](../reviews/f104-mockups-act-like-i-can-interact.md))

- **Q1:** one ticket, built by the lead with the owner in a terminal session: one attribute and a Chromium test. No runner job, escalation or checkpoint. The review added one sentence to the planner's brief and filed one bug ticket.
- **Q3:** no developer work.
- **Q5:** see the review's numbers.
- **Anything else:** the card waited three days behind a developer ticket (f42-01) that nothing moved, while it blocked the owner's review of F54: a one-line fix that unblocks the owner shouldn't queue behind the ticket that shares its lines. The review was handed 158 files for it: a ticket committed in a terminal session carries no `Task:` trailer, so the start tag fell back to the day the card was planted (bug-01). The fix made scripts run, but nothing told the planner what the frame still refuses (storage, dialogs, forms, requests), which would have given the owner the same dead mock-up again; the brief now says it.
- **Decisions affected:** none. F104 D1 (the frame allows scripts and nothing else) is a security decision taken with the owner in the session.

### F72 (2026-10-13): a card that changes a page gets a Today / Proposed mock-up, unasked ([review](../reviews/f72-i-really-like-the-mock-up.md))

- **Q1:** one ticket, a headless lead job on protected runner code, merged first time in 27 minutes for 62 lines. No escalation, direction or checkpoint. The review made one small fix itself and filed no ticket.
- **Q3:** no developer work.
- **Q5:** see the review's numbers.
- **Anything else:** an owner's preference ("this should be the default") became a paragraph in the planner's brief, a line each in `lead.md` and `owner.md`, and a test on the brief. The plan named an example mock-up (F17's) written before the format it asks for existed, and the brief copied it; the review pointed the brief at F94's, which has the switch. When a brief names an example, check the example does what the sentence before it says. Whether planners follow the rule shows only on the next frontend card.
- **Decisions affected:** none. F72 D3 replaces "iterate the mock-up, then write the tickets" with both in one reply.

### F101 (2026-10-13): the standing runner holds instead of ending ([review](../reviews/f101-uv-runner-run-command-stopped-when.md))

- **Q1:** one ticket, a headless lead job on protected runner code, merged first time in 41 minutes. No escalation, direction or checkpoint. The review made one small fix itself and filed a developer ticket and a bug ticket.
- **Q3:** no developer work yet; f101-02 (the dashboard's wording) is the first.
- **Q5:** see the review's numbers.
- **Anything else:** a runner that ends is deaf to the dashboard, and for two days nothing the owner asked was applied: any factory steered from a page needs a run that stays up, or a service that takes requests without one. The fix was right in the loop and wrong on the page: the idle line reads "Running: Idle: …" in green, because the tests read the database and the Done when named the page. The same deafness remains in the sleep to a limit's reset (bug-02). An idle runner now restarts within seconds of any save to its own code, which a terminal session will meet (backlog).
- **Decisions affected:** ADR 17's standing command now never ends by itself; `docs/workflow.md` says so. None changed.

### F13 (2026-10-13): a planted idea shows in Coming at once ([review](../reviews/f13-planting-idea-ui-feedback.md))

- **Q1:** one developer ticket, difficulty 3, about 20 lines of template script. Two sessions, six developer attempts, one direction, two escalations; the second escalation finished it on the branch. No checkpoint ran. The review made one small fix itself and filed no ticket.
- **Q3:** Qwen 0/1. Four attempts stopped with no edit after 10 minutes of reading, two timed out; where it did edit, it replaced a form by hand so htmx never bound the new one, and removed the assertions in two existing tests that showed it.
- **Q5:** see the review's numbers.
- **Anything else:** the owner asked for this on 2026-10-07 and again on 2026-10-08, and it merged on 2026-10-13. Three of the six attempts could not pass whatever they wrote: main was red on a file a review had left (F12's probe), and the ticket was queued without waiting for its removal. The other three met a ticket older than the code it described. Two things a factory needs here: a queue that holds developer tickets while its own gates fail on main, and a ticket's Context re-read against main when it is requeued days later. The developer's removal of assertions from existing tests was caught only because the first of them failed a gate; the session report lists edited tests, but nothing compares their assertions before and after.
- **Decisions affected:** none.

### F22 (2026-10-14): Archive sits at the bottom of a thread ([review](../reviews/f22-move-archive-button-on-planning-desk.md))

- **Q1:** one developer ticket, difficulty 2: two blocks of a template moved as they were. Merged at the first attempt, with no direction, escalation or checkpoint finding. The review added one browser test and filed no ticket.
- **Q3:** Qwen 1/1 first time, 31 minutes of model and 15 of gates, 2.4M tokens read for 59 changed lines. The code was right; its tests compared positions in the HTML text and left the phone's sticky box, the reason for the design, to the review.
- **Q5:** see the review's numbers.
- **Anything else:** a one-sentence request waited six days (planted 2026-10-07, merged 2026-10-13), none of them in the work: it queued behind a red main (f12-03) and its turn. The cheapest work in a factory is also the easiest to leave waiting; a queue could let a difficulty-2 ticket with one file pass ahead when a developer is free. The review again read other work (31 files for one commit): bug-01.
- **Decisions affected:** none.

### F14 (2026-10-14): a waiting plant or message is edited or cancelled ([review](../reviews/f14-coming-planted-ideas-not-clickable.md))

- **Q1:** three tickets: one the lead's (the protected runner), merged first time; two developer tickets at difficulty 4–5, both escalated after three attempts and built or finished by the lead. Two directions, two escalations, no checkpoint. The review made one small fix and filed one lead ticket.
- **Q3:** Qwen 0/2. Five of six attempts stopped with no edit after 10 minutes of reading; the sixth, under a direction, built the thread's buttons in 77 minutes with five faults (among them a redraw listener that never fired, hidden by a `page.reload()` in its own tests) and stopped on an existing test the ticket hadn't named. Claude Opus: $8.89 before the review.
- **Q5:** see the review's numbers.
- **Anything else:** four tickets in a row on the same pages came back to the lead (f9-25, f13-01, f14-02, f14-03), each needing a 1,000-line module, a template with its script and a 2,700-line test file. A direction after two no-edit attempts has not once helped. What a factory needs here is a way to see that a kind of ticket is outside its developers' range and to route it by itself: by the size of the files it must read, not by the lead's difficulty score, which said 4. Second: one of the milestone's acceptance lines reached one ticket and not its twin; nothing checks that every "Done when" of a plan is carried by a ticket.
- **Decisions affected:** none.

### F109 (2026-10-15): merged cards link to each other ([review](../reviews/f109-when-plans-get-merged-i-need.md))

- **Q1:** four tickets: one the lead's with the owner (f109-02, no key reused); two developer tickets at difficulty 4, each merged on its third attempt after a direction; one checkpoint fix ticket (f109-04), escalated and finished by the lead. The review fixed four findings itself, one blocking.
- **Q3:** Qwen 0/3 first time, 20.9M tokens, five attempts ended "no edit after 10 min", all in `test_planning.py`. The checkpoint (Sonnet) found four real flaws and missed the two that mattered.
- **Q5:** see the review's numbers.
- **Anything else:** 25 tests passed while every real merged card's header would have been wrong twice: the fixtures left the merged card's doc on main and its milestones row out, the opposite of a real merge on both counts. Neither the developer, nor the checkpoint, nor the lead's ticket said what a real merge leaves behind; reading the 19 real headings on main showed both bugs in a minute. A factory's tests are only as true as their fixtures, and the cheapest check is one real record beside each hand-built one (now a ticket-writing rule). Second, a direction again didn't stop the no-edit re-reading (F14's lesson, again).
- **Decisions affected:** none.

### F23 (2026-10-16): "Comment…" puts the cursor in the box ([review](../reviews/f23-when-i-click-comment-on-the.md))

- **Q1:** one developer ticket, difficulty 2, 14 lines of template script and one browser test. Merged at the first attempt; one checkpoint nit (confirmed). The review tightened one assertion itself and filed no ticket.
- **Q3:** Qwen 1/1 first time, 56 minutes and 1.0M tokens. It followed the ticket's iPhone note (focus inside the tap, not on `toggle`) exactly; its test checked "a comment box has focus" where Done when said "that point's".
- **Q5:** see the review's numbers.
- **Anything else:** a ticket that explains a platform trap and names the fix is carried out as written; the gap was again between a Done-when line and the assertion behind it (F26's lesson). Nine days from note to merge, none of it in the work.
- **Decisions affected:** none.

### F30 (2026-10-16): a thread shows the latest answer first ([review](../reviews/f30-on-conversations-i-want-to-the.md))

- **Q1:** one developer ticket, difficulty 3, escalated after three attempts and done by the lead on main (reset, not finished). No checkpoint. The review fixed two findings itself and filed no ticket.
- **Q3:** Qwen 0/1, 7.8M tokens over 130 minutes: two no-edit stops, then, under a direction, a branch that duplicated the message markup and bent nine existing tests. The lead's version is about 30 lines.
- **Q5:** see the review's numbers.
- **Anything else:** the ticket was planned a week before the routing rule that would have made it the lead's, and a new rule reached new plans only: 16 more waiting tickets were in the same case until this review moved them. A factory's routing rules need to be applied to its queue when they are made, not only at planning. Second, the tests' threads all ended on a lead message with points; real approved threads end on an approval note, and one look at a real page (F95) showed the leftover counter (F109's lesson: one real record beside each hand-built one).
- **Decisions affected:** none.

### F94 (2026-10-16): While you were away says who, when and how long, once ([review](../reviews/f94-opus-f9-25-seeds-and-planting.md))

- **Q1:** one developer ticket, difficulty 3, merged on the third attempt after a direction. No checkpoint. The review rewrote four weak tests and one wording itself, and filed one developer ticket (f94-02, durations in days).
- **Q3:** Qwen 0/1 first time, 10.2M tokens over 163 minutes for about 30 lines: a timeout, a no-edit stop, then a pass. The code was right; four of its six new tests passed without testing their own ticket's row.
- **Q5:** see the review's numbers.
- **Anything else:** both visible findings ("finished … · finished", "took 142.2 h") came from reading the page on the live database, and neither the mock-up nor the tests could show them. Third milestone running (F109, F30, F94) where a real record found what the hand-built ones hid. Reading the page on real data belongs in the checkpoint or review of every UI ticket (card text in the review, for the owner to plant).
- **Decisions affected:** none.

### F106 (2026-10-21): blocked tickets reach the owner, and the lead looks first ([review](../reviews/f106-where-do-blocked-tickets-go-for.md))

- **Q1:** six tickets: five the lead's (`runner/` is protected), each merged first time and each restarting the runner; one developer ticket (f106-02), merged on its third attempt after a direction. The review fixed one should-fix itself (failed work kept on only one of three ways out of `blocked/`) and filed one developer ticket (f106-07, D4 had no ticket).
- **Q3:** Qwen 0/1 first time on a desk group (two stops, 2.1M tokens); the lead 5/5 on runner work.
- **Q5:** see the review's numbers.
- **Anything else:** both findings sat between tickets, not in one. A decision applied in one ticket and needed by a later one (D3's copy, then f106-05's replan), and a decision no ticket carried (D4). Checkpoints read one ticket at a time and skip lead tickets, so only the review can see this; a plan check that every decision is named by a ticket would catch the second kind (F14's "Done when" lesson, for decisions).
- **Decisions affected:** none.

### F19 (2026-10-21): the desk and an open thread refresh by themselves ([review](../reviews/f19-will-i-need-to-refresh-planning.md))

- **Q1:** three developer tickets: f19-01 (desk poll, `liveIdle` waits while typing) merged first time; f19-02 (one Overview poll) on its third attempt after a direction; f19-03 (a checkpoint's fix ticket: a browser test for f19-02) on its third. Two checkpoints, four findings, all confirmed. The review fixed three findings itself, one blocking, and filed no ticket.
- **Q3:** Qwen 1/3 first time, 24.9M tokens over 294 minutes of model for about 30 lines of template and script. Five of its six failed attempts were no-edit stops or timeouts.
- **Q5:** see the review's numbers.
- **Anything else:** the card's headline ("the lead's answer appears on an open thread") was carved out of f19-01 as "the lead's", and no lead ticket was ever written; three tickets merged, two checkpoints passed, and the outcome the owner asked for was not built. A plan check that every Done-when line is carried by a ticket (F14 and F106 said the same) would have caught it at planning. Second, an attribute moved into a partial shared by every page (`hx-swap-oob` in `/live`) logged errors on every other page; checkpoints read the diff, not who else includes the file.
- **Decisions affected:** none.

### F28 (2026-10-21): Pause and Resume hold what you asked through the 5 s refresh ([review](../reviews/f28-the-first-time-i-clicked-on.md))

- **Q1:** two developer tickets. f28-01 (the top bar's script) merged on its third attempt after a direction (a no-edit stop, a timeout); f28-02 escalated after three attempts and the lead built it, because the ticket asked to remove buttons that a protected test asserted (the lead's ticket at fault; lesson in `docs/task-writing.md`). One checkpoint, no findings. The review fixed four findings itself (two should-fix, two nits) and filed no ticket.
- **Q3:** Qwen 0/2 first time, 13.4M tokens and about 2 hours of model for 48 lines of script.
- **Q5:** see the review's numbers.
- **Anything else:** f28-01's stale-poll tests passed without the fix: they waited for the final state within two polls, so a stale bar swapped in and then replaced still ended right. The checkpoint read them and called them sound. "Fail without the change" is in every ticket and checked by nobody for each test; a test of a race must assert in the window the race opens, not after it.
- **Decisions affected:** none.

### F135 (2026-10-21): reviews stopped at once on end-to-end tests the split removed ([review](../reviews/f135-why-is-there-a-couple-of.md))

- **Q1:** one lead ticket (protected `runner/`), merged first time; no checkpoint, a clean review round with no findings. Its own Done when (F28 and F19 reviewed without a command) was met by the runner within the hour.
- **Q3:** Claude only, ≈272k token-equivalents; no local tokens, as fits protected code.
- **Q5:** see the review's numbers.
- **Anything else:** the cause was fixed in a terminal session on 2026-10-15 (`[checks] e2e`), but the two stops it had already recorded stayed on Needs you six more days, until this ticket. A fix that removes a stop's cause should clear the stops it recorded in the same change. The owner planted the same question twice (F135, F156): a stop on Needs you should say whether it will clear by itself.
- **Decisions affected:** none.

### F151 (2026-10-22): each batch gets its stand-in while the checkpoint waits for Claude ([review](../reviews/f151-i-had-to-restart-the-runner.md))

- **Q1:** one lead ticket (protected `runner/`), merged first time in 13.5 minutes; no checkpoint. Review round 1: one should-fix (an acceptance case untested, fixed by the review) and one nit (backlog).
- **Q3:** Claude only, $0.84 for the ticket; no local tokens, as fits protected code.
- **Q5:** see the review's numbers.
- **Anything else:** the bug lived behind a test that drove the parked row by hand, so the loop never had to start it. A scheduling rule's test should go through `work_queue`; and a "falls back as today" acceptance case should take the new path before falling back.
- **Decisions affected:** none; F140 would make the fix's branch unnecessary.

### F153 (2026-10-22): Sonnet can take the easier lead tickets, Opus steps in when it fails ([review](../reviews/f153-i-wonder-if-sonnet-would-be.md))

- **Q1:** two lead tickets (protected `runner/`), both merged first time on Opus (17 and 6 minutes); no checkpoint. Review round 1: one should-fix (the workflow docs didn't say who does a lead ticket now; fixed by the review) and three nits (backlog).
- **Q3:** Claude only, $2.94 for the two tickets, under ADR 32's $5 estimate; no local tokens, as fits protected code.
- **Q5:** see the review's numbers.
- **Anything else:** nothing changes until the machine's `factory.toml` gets ADR 32's two lines (D7); the trial (ADR 32 item 6) starts then. Its pass rate must be read from tickets and step-up jobs, since a lead job's `jobs.outcome` is its session's, not its `check-all`'s.
- **Decisions affected:** ADR 32 is now code; its item 6 trial is the next factory question.

### F154 (2026-10-23): one Planted column, a "growing" tag, and each stage says what comes next ([review](../reviews/f154-what-s-the-difference-between-planted.md))

- **Q1:** one lead ticket (a stage list read by three pages, a script and many tests, D5), merged first time in 22 minutes; no checkpoint. Review round 1: two nits (a narrowed test, two stale comments), both fixed by the review.
- **Q3:** Claude only: $4.69 planning, $3.38 building; no local tokens.
- **Q5:** see the review's numbers.
- **Anything else:** the card waited two days on f152-01, whose local developer took four hours before the lead's escalation; a ticket touching the same lines as a lead ticket might as well be the lead's. "An edited test cut to its first rows" recurred (F173, F154) and is now in `docs/agents/developer.md` rule 13.
- **Decisions affected:** none.

### F114 (2026-10-23): one notification per look, named after its card, opening its page ([review](../reviews/f114-i-want-to-be-notified-only.md))

- **Q1:** two developer tickets, both merged on the second attempt after a timeout; then eight fix tickets from three checkpoints (two by Copilot standing in for Claude), six of them on the same browser tests, over six days. f114-07 took three attempts and a direction. Review round 1: three should-fix and three nits fixed by the review, one nit to the backlog.
- **Q3:** Qwen only for the building, about 15 hours of model for roughly 200 lines of code: 5 hours on the two feature tickets, 10 on fixes; Claude $4.82 (planning, one direction, one checkpoint) before the review.
- **Q5:** see the review's numbers.
- **Anything else:** a chain of fix tickets on tests is a sign the cause is elsewhere. Here the stand-in service workers broke `notify.js` on load, and the developer hid that behind test hooks in production code; each checkpoint judged the newest test and missed the hook. Lesson in `docs/agents/lead.md` (Known range, F114): a second finding on tests a fix ticket of the same card already rewrote is the lead's to fix.
- **Decisions affected:** none.

### F142 (2026-10-23): notifications from every project, and to a closed phone through ntfy ([review](../reviews/f142-why-am-i-not-getting-notifications.md))

- **Q1:** two lead tickets (the ntfy sender, protected `runner/`; the phone's steps), each merged first time on Opus (14 and 5 minutes); one developer ticket (every project's notices) merged first time in 77 minutes, then one checkpoint fix ticket, first time in 62 minutes. Review round 1: three should-fix (one fixed by the review, two to developer tickets f142-04 and f142-05) and two nits fixed by the review.
- **Q3:** Claude $4.12 building the two lead tickets and $0.24 for the checkpoint; planning $22.82 over five planner jobs, including ADR 31; the local model 9.9M tokens in for the two developer tickets.
- **Q5:** see the review's numbers.
- **Anything else:** the checkpoint caught the id mismatch but not the two other slips in the same diff (words without the card's titles; one "all done" flag for every project). A worded notice's test should use a kind whose words depend on the data (a reply, not an `adr`), or it can't see missing titles.
- **Decisions affected:** ADR 31 is now code.

### F90 (2026-10-23): a card's page shows the owner's whole note ([review](../reviews/f90-editing-seeds-that-i-ve-planted.md))

- **Q1:** one lead ticket (difficulty 3), taken by Sonnet under ADR 32: its work was right, but a flaky `test_loop.py` timing test failed its `check-all`, so Opus stepped up, found the work correct and passed the gate on a rerun (two timing tests failed in turn). No checkpoint. Review round 1: one should-fix fixed by the review (the factory's merge headings and escapes showed raw in the note), one should-fix to the backlog (the flaky tests).
- **Q3:** Claude only: $0.88 planning, $0.60 building (Sonnet $0.28, Opus $0.32); no local tokens.
- **Q5:** see the review's numbers.
- **Anything else:** ADR 32's trial counts a step-up as Sonnet failing; here the failure was the gate's. Read the step-up job's log before counting it against Sonnet. The ticket named `.factory/milestones/`, the cards' old folder; the lead used `cards/`.
- **Decisions affected:** none.

## 10. For the owner to decide at review time (each item can be accepted on its own)

1. 4.1: queue mode by default, and park the automated review loop.
2. 4.2 and 4.3: a separate factory repo, configured per project by `factory.toml`.
3. 4.4: FRONTIER.md plus pointer files.
4. 4.5: one report per milestone.
5. Whether to extract at all (Q7), and if so, when.
