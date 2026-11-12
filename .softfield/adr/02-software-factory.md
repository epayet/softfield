# ADR 02: Extract the workflow into a reusable "software factory"

- **Status:** Draft, **work in progress**. Not for decision yet. Review after M3 or M4, whichever comes first with at least ~15 tasks of evidence.
- **Date:** 2026-09-28 (first draft)
- **Deciders:** project owner (accepts), Claude (drafts)
- **Evidence:** `.softfield/reviews/m1.md`, ADR 01, `.softfield/sessions/`

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
| `gitops.py`, `state.py`, `report.py` | `.softfield/protected-paths.txt` | Tool-allow syntax (`Bash(uv run pytest:*)`) |
| `local_model.py` (warm-up, `opencode run`, token parsing) | Dependency files and dirs (`pyproject.toml`, `uv.lock`, `vendor/`) | ESCALATION/REVIEW prompt wording ("Follow CLAUDE.md") |
| File-level gates: allowed files, protected, existing tests unchanged, deps, max_diff, BLOCKED | Layout rule (`tests/unit` ↔ `coucou/`), i18n gate (`runner/i18n.py`) | `CLAUDE.md` as the frontier's instruction file |
| LOCAL/RETRY/FRESH prompts, with the project's check commands filled in | AGENTS.md **code** rules (§Code, §What to read), task id prefix | The headless section of `docs/workflow.md`; the prices in `runner.toml` |
| Protocols: BLOCKED categories, discoveries, the `escalated/` queue, review grading | Test tiers, the e2e trigger command | `.github/copilot-instructions.md`, if Copilot is used |

## 3. What the frontier actually has to do

- **Interactive, with the owner:** milestone planning, ADRs, skeletons and failing tests, reference implementations, protected-path code, reviews, the French check, and reports. This is almost all of the frontier's value. **Any capable agentic coding tool can do it**: it has to read, edit, run shell commands and follow an instructions file.
- **Headless, inside the runner:** escalations and review rounds. Both can wait. An escalated task already sits in `.softfield/tasks/escalated/` with its logs and last diff, the runner already carries on with independent tasks, and `--no-escalate` already exists.

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
- By default, escalated tasks wait in `.softfield/tasks/escalated/`. The milestone review is interactive: the frontier and the owner do it together, with the same grading and routing rules (`docs/workflow.md` §Milestone review loop).
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

### 4.3 A per-project `factory.toml` replaces `.softfield/project.toml`

```toml
[project]
name = "coucou"
src = ["coucou"]
dependency_files = ["pyproject.toml", "uv.lock"]
dependency_dirs = ["coucou/static/coucou/vendor/"]
protected = ".softfield/protected-paths.txt"

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
- Q1–Q8: answers with evidence (link .softfield/reviews/mN.md, .softfield/sessions/…)
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
- **Anything else:** both features were already in real use before the review: a copy in `~/Dropbox/software-factory-backups` and five threads in `.softfield/planning/`. Reading the real exports showed the lead's points twice in each reply (text and boxes), which is the planner prompt's doing and already F41's fix. The review found no code defect; it added the restore steps (a backup nobody knows how to restore is half a backup) and one test.
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

- **Q1:** five tickets, one merged by the runner first time (a headless lead ticket), three built by the lead in a terminal with the owner, one done headless then landed by hand after two days behind the weekly reserve and a red main. No escalation, direction or checkpoint. A sixth ticket waits in `.softfield/tasks/later/` for a mock-up.
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

- **Q1:** two developer tickets. f28-01 (the top bar's script) merged on its third attempt after a direction (a no-edit stop, a timeout); f28-02 escalated after three attempts and the lead built it, because the ticket asked to remove buttons that a protected test asserted (the lead's ticket at fault; lesson in `runner/instructions/task-writing.md`). One checkpoint, no findings. The review fixed four findings itself (two should-fix, two nits) and filed no ticket.
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
- **Anything else:** the card waited two days on f152-01, whose local developer took four hours before the lead's escalation; a ticket touching the same lines as a lead ticket might as well be the lead's. "An edited test cut to its first rows" recurred (F173, F154) and is now in `.softfield/developer.md` rule 13.
- **Decisions affected:** none.

### F114 (2026-10-23): one notification per look, named after its card, opening its page ([review](../reviews/f114-i-want-to-be-notified-only.md))

- **Q1:** two developer tickets, both merged on the second attempt after a timeout; then eight fix tickets from three checkpoints (two by Copilot standing in for Claude), six of them on the same browser tests, over six days. f114-07 took three attempts and a direction. Review round 1: three should-fix and three nits fixed by the review, one nit to the backlog.
- **Q3:** Qwen only for the building, about 15 hours of model for roughly 200 lines of code: 5 hours on the two feature tickets, 10 on fixes; Claude $4.82 (planning, one direction, one checkpoint) before the review.
- **Q5:** see the review's numbers.
- **Anything else:** a chain of fix tickets on tests is a sign the cause is elsewhere. Here the stand-in service workers broke `notify.js` on load, and the developer hid that behind test hooks in production code; each checkpoint judged the newest test and missed the hook. Lesson in `runner/instructions/lead.md` (Known range, F114): a second finding on tests a fix ticket of the same card already rewrote is the lead's to fix.
- **Decisions affected:** none.

### F142 (2026-10-23): notifications from every project, and to a closed phone through ntfy ([review](../reviews/f142-why-am-i-not-getting-notifications.md))

- **Q1:** two lead tickets (the ntfy sender, protected `runner/`; the phone's steps), each merged first time on Opus (14 and 5 minutes); one developer ticket (every project's notices) merged first time in 77 minutes, then one checkpoint fix ticket, first time in 62 minutes. Review round 1: three should-fix (one fixed by the review, two to developer tickets f142-04 and f142-05) and two nits fixed by the review.
- **Q3:** Claude $4.12 building the two lead tickets and $0.24 for the checkpoint; planning $22.82 over five planner jobs, including ADR 31; the local model 9.9M tokens in for the two developer tickets.
- **Q5:** see the review's numbers.
- **Anything else:** the checkpoint caught the id mismatch but not the two other slips in the same diff (words without the card's titles; one "all done" flag for every project). A worded notice's test should use a kind whose words depend on the data (a reply, not an `adr`), or it can't see missing titles.
- **Round 2 (2026-10-28):** f142-04 (local, first attempt, 37 minutes) and f142-05 (the lead, Sonnet, $0.79) resolved both; the review added one test and removed a duplicate mark. f142-05 was routed "local" but touches protected `runner/`, so it became a lead ticket and waited four days behind Claude's weekly reserve and limits for a ten-line change. A review fix of about 20 lines in protected code is the review's own (lead.md already says so); the router's "local" there was a slip, not a rule gap.
- **Decisions affected:** ADR 31 is now code.

### F90 (2026-10-23): a card's page shows the owner's whole note ([review](../reviews/f90-editing-seeds-that-i-ve-planted.md))

- **Q1:** one lead ticket (difficulty 3), taken by Sonnet under ADR 32: its work was right, but a flaky `test_loop.py` timing test failed its `check-all`, so Opus stepped up, found the work correct and passed the gate on a rerun (two timing tests failed in turn). No checkpoint. Review round 1: one should-fix fixed by the review (the factory's merge headings and escapes showed raw in the note), one should-fix to the backlog (the flaky tests).
- **Q3:** Claude only: $0.88 planning, $0.60 building (Sonnet $0.28, Opus $0.32); no local tokens.
- **Q5:** see the review's numbers.
- **Anything else:** ADR 32's trial counts a step-up as Sonnet failing; here the failure was the gate's. Read the step-up job's log before counting it against Sonnet. The ticket named `.softfield/milestones/`, the cards' old folder; the lead used `cards/`.
- **Decisions affected:** none.

### F68 (2026-10-28): the dashboard is called SoftField ([review](../reviews/f68-i-want-the-factory-to-be.md))

- **Q1:** one developer ticket (difficulty 3), merged on the second attempt in 101 minutes; then six fix tickets from checkpoints (four by Copilot standing in for Claude), five of them on one regression test over a week (f68-03 to f68-07), all first time but one. Review round 1: one blocking (the logo's link never reached the Overview from another page), two should-fix (doubled titles; the name cut to "SoftFi" on a phone) and two nits, all fixed by the review; one should-fix to a lead ticket (f68-08).
- **Q3:** Qwen only for the building, about 7.2 hours of model for some 40 lines of product: 1.7 on the feature, 1.6 on f68-02, 3.9 on the regression-test chain. Claude's share is in the review's numbers.
- **Q5:** see the review's numbers.
- **Anything else:** six checkpoints read the brand's tests closely and none clicked the link: the blocking bug was in f68-01's three-line template diff, and its test asserted the wrong href. A checkpoint on a UI ticket should check each Done when against the code, not only the tests' strength. And F114's "fix of a fix is the lead's" rule, written the day f68-07 was filed, didn't reach the checkpoints; f68-08 makes it a check.
- **Decisions affected:** none.

### F69 (2026-10-28): a button to switch between light and night ([review](../reviews/f69-i-want-a-button-to-switch.md))

- **Q1:** one developer ticket (difficulty 3), merged on the second attempt after a timeout; then five fix tickets from checkpoints (four by Copilot standing in for Claude), four of them on the same two browser tests (f69-03 to f69-06); f69-06 took five attempts, a direction and a 3.8-day park. Review round 1: four should-fix and one nit, all fixed by the review.
- **Q3:** Qwen only for the building, about 8.2 hours of model for some 60 lines of product: 2.6 on the feature, 5.6 on fixes; Claude $0.69 for one direction before the review.
- **Q5:** see the review's numbers.
- **Anything else:** the third card running (F114, F68, F69) where a test finding became a chain of developer tickets that never fully closed it; all three ran before f68-08. Again the checkpoints missed edge bugs in the feature diff (a selector that lost its theme scope, a stored choice the system could override, a 22 px tap target) while judging the newest test. A mechanical media-query-to-attribute rewrite needs each comma-separated selector rescoped; now a test.
- **Decisions affected:** none.

### F80 (2026-10-28): the Agents page shows each agent's score by kind of work ([review](../reviews/f80-developer-rating-could-be-more-tailored.md))

- **Q1:** one developer ticket (difficulty 4). Qwen's attempt 1 was right and failed only `all-tests`, on a test main itself failed. Attempt 2 blocked `needs-file`, as developer rule 11 says. The ticket waited about 16 hours parked for Claude, then an Opus escalation finished it on the branch in 6 minutes. No checkpoint. Review round 1: two nits fixed by the review, one should-fix to a lead ticket (f80-02: a red main spares the developer's attempts).
- **Q3:** Qwen about 1.4 hours of model (11.2M tokens in) on work that was mostly right; Claude $1.56 for the escalation. The plan's cost is in the review's numbers.
- **Q5:** see the review's numbers.
- **Anything else:** F106's main-red guard holds lead tickets only, so a developer still burns its attempts on a red main, and its rating records two "not merged" games for code that merged. The new bay already shows the Known range's split: Qwen does better than rated on code without pages (+6 over 60 tickets) and as rated on pages (−2 over 114).
- **Decisions affected:** none. A rating per kind stays deferred, as the card's Later says.

### F82 (2026-10-28): text boxes grow with what you type ([review](../reviews/f82-the-plant-idea-text-box-is.md))

- **Q1:** one developer ticket (difficulty 2). Qwen's attempt 1 was right and failed only `all-tests`, on a red main (the same trap as F80, before f80-02 landed). Attempt 2 stopped with no edit; the ticket then sat about 18 hours parked for a Claude direction ($0.47), and the last attempt passed. One checkpoint nit (a loose height check). Review round 1: one should-fix (the focus half of the script threw on every focus, so a box filled by Try again never fitted) and one nit, both fixed by the review.
- **Q3:** Qwen about 1.4 hours of model for 16 lines of script and one CSS rule; Claude $0.78 for the plan and $0.47 for the direction.
- **Q5:** see the review's numbers.
- **Anything else:** a copy-pasted handler with one changed line (`tagName ===` for `closest`) made the variable a boolean. The ticket's Done when named the focus path only in its Context, so no test pressed it, and the checkpoint judged the tests it saw. A Done when line for each path the plan names would have caught it.
- **Decisions affected:** none.

### F84 (2026-10-28): Coming says which reply the lead is writing ([review](../reviews/f84-when-the-planner-is-replying-to.md))

- **Q1:** one developer ticket (difficulty 3) that Qwen failed three times (33 min failed, 78 min timeout, 20 min with no edit under an Opus direction), then about 16 hours parked before the direction. An Opus escalation built it in 43 minutes, about 120 lines and 7 tests. No checkpoint (lead work). Review round 1: two should-fix (Coming put a held reply before a message not yet picked up, against D4; the new "Writing now" words were hard to read in the light theme), both fixed by the review, and one nit to the backlog.
- **Q3:** Claude $1.51 for the plan, $0.64 for the direction, $3.79 for the escalation; Qwen about 2.2 hours of model with nothing merged.
- **Q5:** see the review's numbers.
- **Anything else:** the third time (F30, F172, F84) a plan routed a ticket touching `test_planning.py` and several functions of one page to the developer after the Known range said it was the lead's: a rule only in `runner/instructions/lead.md` doesn't reach the planner's routing. F143 rewrites the rule after splitting the file; the rule it ends on wants a pre-flight check, not another line.
- **Decisions affected:** none.

### F51 (2026-10-28): the desk counts only what waits on you ([review](../reviews/f51-when-a-plan-depends-on-an.md))

- **Q1:** two developer tickets (f51-03, difficulty 2, and its checkpoint fix f51-04), both first time by Qwen; two lead tickets (f51-01, f51-02, difficulty 4, one in protected runner code), both first time by Sonnet. One Copilot checkpoint finding, confirmed. Review round 1: two should-fix (the runner's guard reached past D3 to ADRs already on main; the desk doubled the card's name in every bundle title) and two nits (a weakened test, a duplicate test), all fixed by the review.
- **Q3:** Opus $19.89 for five planner replies (three cards merged into the plan, then F176's replan, still open) against Sonnet $1.15 for the lead tickets; Qwen about 32 minutes of model.
- **Q5:** see the review's numbers.
- **Anything else:** Sonnet's lead work was right in substance and loose at the edges: tests pinned the doubled titles a look at real data shows, an old assertion was weakened to `!=`, a guard was wider than its decision. The planning cost seventeen times the build.
- **Decisions affected:** none.

### F74 (2026-10-28): a conversation keeps one box on the desk ([review](../reviews/f74-when-i-reply-to-a-your.md))

- **Q1:** one lead ticket (difficulty 3, planned as a developer's), merged first time by Sonnet in 21 minutes; no checkpoint. Review round 1: one should-fix (the rewritten query re-sorted "Your answers wanted" by thread start, not the lead's latest reply) and one nit (Coming's thread markup left unreachable), both fixed by the review.
- **Q3:** Claude only, Sonnet $0.94 for the build; no local tokens.
- **Q5:** see the review's numbers.
- **Anything else:** Sonnet turned ten existing tests into the same checks on the new place without weakening any, the opposite of F51's loose edges. Again an edge slipped where no test held it: a merged query lost its `ORDER BY`.
- **Decisions affected:** none.

### F100 (2026-10-28): proposals show "being revised" while the owner's message waits ([review](../reviews/f100-if-i-replied-to-a-conversation.md))

- **Q1:** one lead ticket (difficulty 3), merged first time by Sonnet in 12 minutes; no checkpoint. Review round 1: one should-fix (the general thread's proposal path untested) and two nits (a duplicated wording loop, a test name contradicting its new assertion), all fixed by the review.
- **Q3:** Claude only, Sonnet $0.93 for the build; no local tokens.
- **Q5:** see the review's numbers.
- **Anything else:** D1's "one rule" was lifted cleanly and read by three pages. Second milestone running where Sonnet leaves one branch untested (F74: an `ORDER BY`; here, the general thread).
- **Decisions affected:** none.

### F42 (2026-10-29): the review page and the top bar give a phone's screen to the content ([review](../reviews/f42-the-space-for-me-to-scroll.md))

- **Q1:** two developer tickets (difficulty 3, CSS and a little JS). Neither passed first time: f42-01 stopped twice for "no edit after 20 min" and was finished by the lead; f42-02 stopped twice the same way and passed on its third attempt (51 min). One Sonnet checkpoint nit (no scroll threshold), confirmed. Review round 1: one should-fix (that same threshold, which the ticket had asked for: fixed by the review, with a test), one should-fix (a twelve-line setup copied into four tests: ticket f42-03) and one nit (the phone loaded the hidden mock-up frame: fixed).
- **Q3:** Opus about $2 on the f42 jobs (two directions, one escalation) and Sonnet $0.16 for the checkpoint; Qwen about 131 minutes of model, 80 of them in four stalled attempts.
- **Q5:** see the review's numbers.
- **Anything else:** layout that has to be measured in a browser stalls Qwen even with the cause named in a direction; f42-02 passed but dropped one sentence of its ticket (the 8 px threshold), and its test couldn't catch it because the test only checked big scrolls. A ticket's numbers want a test that pins them.
- **Decisions affected:** none.

### F21 (2026-10-29): the lead's briefs ([review](../reviews/f21-lead-briefs.md))

- **Q1:** three lead tickets. f21-01 (where the work stands, for the planner) and f21-02 (lead.md's sections pasted into every lead prompt) were done first time by Opus on 12 October, but blocked by a stray test file on main failing the layout gate, and landed by hand. f21-03 (trim owner.md) ran twice, changed nothing both times (no target was possible without rewording rules), and was set aside. No checkpoint. Review round 1: one should-fix (owner.md reached every headless lead job twice, through CLAUDE.md's import and the brief) and one nit (the block didn't explain a ticket pulled early by F173), both fixed by the review.
- **Q3:** Claude only: Opus $4.04 for the two built tickets, $1.13 (Opus and Sonnet) for f21-03's two empty runs; no local tokens.
- **Q5:** see the review's numbers.
- **Anything else:** a plan that pastes text into prompts must account for what the agent loads by itself (CLAUDE.md and its imports); and a word-count target on a document that keeps gaining rules can't hold. The card sat over two weeks between its build and its review, mostly behind f21-03.
- **Decisions affected:** none.

### F32 (2026-10-30): the lead window says when it resets ([review](../reviews/f32-the-5-hour-lead-s-window.md))

- **Q1:** one developer ticket (difficulty 2, two template lines). Six Qwen attempts over two runs, none merged. On 2026-10-10 the second attempt had it right but the layout gate failed on a review's stray test file; the ticket was requeued behind its removal with a "The branch so far". By 2026-10-29 that branch was gone, so three attempts read for 20 minutes each for lines that weren't there. An Opus escalation finished it in 10 minutes. No checkpoint. Review round 1: one should-fix (no check for a stale "The branch so far"), fixed by the review with a pre-flight check.
- **Q3:** Claude only on the merged work: Opus $1.87 over a direction and two escalations; Qwen about 2.5 hours of model with nothing merged.
- **Q5:** see the review's numbers.
- **Anything else:** the second ticket (after F17) lost to one day's stale requeues, and the second time a lesson was written as a line before it became a check. Two lines of template took 19 days, almost all of it waiting on another card's fix.
- **Decisions affected:** none.

### F15 (2026-10-30): reorder from the board ([review](../reviews/f15-reprioritising-tickets.md))

- **Q1:** ten tickets. Six lead tickets (the `reorder` request, the order on the board, the field, drag and send, the replan, the arrows' removal) passed first time on Opus. f15-08 (developer, "waits for F22") passed on Qwen's second attempt after a timeout; a stand-in checkpoint (copilot-auto) found two weak points, whose fix tickets f15-09 and f15-10 took three attempts and a direction, and one attempt. f15-06 (the ⋯ actions) stopped three times with no edit on a slow night and was escalated. Review round 1: one should-fix fixed by the review (a card waiting on a bug read "waits for BUGS"), one should-fix ticket (f15-11: a refused send is untested), one factory should-fix as a lead bug ticket (bug-48: skip the direction on a slow night), two nits fixed, one to the backlog.
- **Q3:** Opus $14.17 on the milestone's own jobs ($11.36 of it the six lead tickets); Qwen about 7.2 hours of model, 1 hour of it on f15-06 with nothing to show.
- **Q5:** see the review's numbers.
- **Anything else:** the plan's "Who builds" was right: the parts with a new module, script or phone layout went to the lead and passed at once; the small ticket that went to Qwen merged, but cost two fix tickets and 4 hours of model for 4 lines. The fifth no-edit escalation in two nights made a lesson that had stayed a line in `lead.md` into a ticket (bug-48).
- **Decisions affected:** none.

### F73 (2026-10-30): set a proposal aside ([review](../reviews/f73-i-want-to-be-able-to.md))

- **Q1:** two developer tickets at difficulty 4, both Qwen 0/3 with no edit (2–5 steps per 20-minute attempt), both given a direction at the second failure and both finished by an Opus escalation in one session. Review round 1: one should-fix fixed by the review (a Set aside on its way vanished on a reload), one nit fixed (two CSS rules joined on one line), two nits to the backlog.
- **Q3:** Opus $4.58 on the milestone's jobs ($1.10 of it two directions that changed nothing); Qwen 2 hours of model with nothing merged.
- **Q5:** see the review's numbers.
- **Anything else:** the same no-edit stop as f26-02 and f15-06 in the same two nights; bug-48 (ready, from F15's review) skips the direction on such a night. The plan's "D" for both tickets was wrong for that week's model: a template-plus-SQL ticket against a 2,000-line test file.
- **Decisions affected:** none.

### F103 (2026-10-30): seeds no longer count as waiting for you ([review](../reviews/f103-the-number-of-things-in-planning.md))

- **Q1:** one developer ticket at difficulty 2 (a one-line filter in `waiting_for_you`, four test files). Qwen 0/3, every attempt stopped "no edit after 20 min" with 2, 2 and 10 steps, the third under a line-numbered direction; an Opus escalation finished it in 8 minutes. No checkpoint. Review round 1: no defect; one nit fixed (the Known range line pointed at bug-48).
- **Q3:** Opus $2.46 on the milestone's jobs (planner $0.78, a direction $0.51 that changed nothing, the escalation $1.17); Qwen 1 hour of model with nothing merged.
- **Q5:** see the review's numbers.
- **Anything else:** the fourth ticket of the 2026-10-29 09:14 run to stop this way, and the smallest: even a one-line filter didn't get an edit that night, so the size of the ticket wasn't the cause. Its direction waited 5 hours for Claude's window. bug-48 is the fix.
- **Decisions affected:** none.

### F146 (2026-10-30): the board's developer's view ([review](../reviews/f146-some-kind-of-view-or-toggle.md))

- **Q1:** one lead ticket (Sonnet, passed at its second try after a limit park of about 6 hours) and one developer ticket at difficulty 3 (lever, macro, CSS, tests). Qwen 0/3: two no-edit stops, then a directed attempt that called a macro with an argument it doesn't take and broke every board page. An Opus escalation finished it in 13 minutes. No checkpoint. Review round 1: one should-fix (a fully merged card read "lead only") and one nit (a test that couldn't fail), both fixed by the lead.
- **Q3:** see the review's numbers; Qwen 2 h 15 of model with nothing merged.
- **Q5:** see the review's numbers.
- **Anything else:** same night shape as F103 and F172; bug-48 is the fix. The view itself gives the queue's answer to "what keeps the local model fed": 11 of 97 ready tickets, and a handful of lead tickets (f132-02, f9-29) hold most of the rest.
- **Decisions affected:** none.

### F185 (2026-10-30): answers before proposals, newest answer first ([review](../reviews/f185-i-changed-my-mind-i-want.md))

- **Q1:** one developer ticket at difficulty 2 (swap two `DeskGroup` lines, reverse one loop). Qwen 0/3, all "no edit after 20 min", the third under a direction; an Opus escalation did it on main in 18 minutes. No checkpoint. Review round 1: no findings.
- **Q3:** Opus $1.82 on the ticket (direction $0.59, escalation $1.23); Qwen 1 hour of model with nothing merged.
- **Q5:** see the review's numbers.
- **Anything else:** the ticket named the group-order tests but not three others that pinned the old order (inside the group, Previous and Next, Needs you), so even correct code would have failed the gates; now a line in `runner/instructions/task-writing.md`. The sixth no-edit night ticket; bug-48 is the fix.
- **Decisions affected:** none.

### F175 (2026-11-03): the factory cleans up its temp files ([review](../reviews/f175-if-i-leave-the-factory-running.md))

- **Q1:** three lead tickets, all first time (Sonnet 2/2, Opus 1/1), 30 minutes of work; no escalation or checkpoint. Review round 1: two should-fix and three nits fixed by the review, two nits only reported; round 2 held all five fixes and corrected one figure in the report. The review itself finished four days after the merges, its first run interrupted.
- **Q3:** no developer work (protected runner code).
- **Q5:** see the review's numbers.
- **Anything else:** measuring first changed the fix: the plan blamed killed jobs, the measure found sample hooks in test repos. But the measure itself read length rather than disk use, and its tests couldn't tell: a tool that reports a quantity needs a test that separates it from its near neighbour. Housekeeping added to a path every command takes must not be able to fail that path (the temp folder on a full disk). The 30 GB is still not fully explained; the owner's check on their computer settles it.
- **Decisions affected:** none. ADR 39 waits for the owner.

### F127 (2026-11-03): the factory is optional ([review](../reviews/f127-shared-rules-stay-shared-across-projects.md))

- **Q1:** one lead ticket, one commit of 103 files built in a terminal session, so no checkpoint. Review round 1: two blocking, three should-fix and one nit fixed by the review; one nit set aside (bug-54), three only reported. Round 2: the fixes hold, no code changed, three more nits only reported.
- **Q3:** no developer work (protected runner code and instructions).
- **Q5:** see the review's numbers.
- **Anything else:** 2,926 passing tests missed a command that did nothing, because they called the function behind it and never the command. Moving a file into a protected folder changed which gate applies to it, and only one of the two had the exception. The review was told its commits were "none", since the ticket was written after the commit; the runner now says where to look.
- **Decisions affected:** ADR 41's Consequences says removing the factory means deleting its folder, and one git setting stays too. The folder's README says so; the ADR's text is the owner's and is unchanged.

### F139 (2026-11-03): the folder is `.softfield` ([review](../reviews/f139-the-factory-folder-should-actually-be.md))

- **Q1:** no ticket ran: the owner moved all three projects in a terminal session, with a one-shot script guarded by each project's full check, so no checkpoint saw it and f139-02 was dropped. Review round 1: one blocking and one should-fix fixed by the review, one should-fix set aside (bug-55), three nits only reported. Round 2: the blocking fix didn't work on the real branches, so it was reopened (f139-03), and the regression it caused was fixed.
- **Q3:** no developer work (protected runner code, git and the database).
- **Q5:** see the review's numbers.
- **Anything else:** every check passed on the moved tree, yet the plan's promise that moved branches could still be approved wasn't true: a moved branch's diff since it left main was the whole move, 1,115 files for F133. A check on a tree says nothing about what git compares across history. A blind text pass also rewrites the one document that needs both names. Round 1's fix passed tests that modelled the fault in one file, while all five real branches clash in 95 to 169 places: a fix for a fault seen on live data has to be tried on that data.
- **Decisions affected:** none.

### F170 (2026-11-03): the desk offers the lead's fix, and a blocked ticket's page says why ([review](../reviews/f170-there-s-a-blocked-ticket-that.md))

- **Q1:** one lead ticket merged first time; four developer tickets, one of them (f170-04) escalated after three attempts and finished by Opus. Three checkpoints, one by Copilot standing in for Claude. Review round 1: seven should-fix and two nits fixed by the review, one set aside (bug-57), and two only reported.
- **Q3:** Qwen passed f170-03 and both fix tickets, f170-05 on its second attempt. It failed f170-04, whose `files:` span two pages' modules, the route the plan should have given the lead. Sonnet passed f170-02 first time.
- **Q5:** see the review's numbers.
- **Anything else:** the first checkpoint's finding had three parts and its fix ticket took one and a half: the words stayed, the bug ticket's label stayed, and f170-06, told to fix the tests, wrote the wrong label into one. The next checkpoint read "the screen matches the ticket" from the tests, not the ticket. A fix ticket's finding needs its parts as separate Done when lines. Tests built their own proposals and lead replies, so nothing met real threads, where the lead says other things after its fix ("Approved by the owner…" is a lead message too).
- **Decisions affected:** none. bug-57 makes pre-flight refuse a developer ticket that spans two pages, the check F84, F172 and F170 have now each wanted.

### F85 (2026-11-03): real before and after pictures at sign-off ([review](../reviews/f85-when-i-sign-off-a-task.md))

- **Q1:** three lead tickets, all merged, one parked about three hours for a Claude limit; no checkpoint. Review round 1: one blocking, four should-fix and two nits fixed by the review, one nit set aside (bug-58), two only reported.
- **Q3:** no developer work (protected runner code; the dashboard ticket serves files from disk).
- **Q5:** see the review's numbers.
- **Anything else:** the blocking bug was found because the card reviewed itself: the brief said "mock-up: none" while the card's doc named its mock-up. Its test used `f1` as the card's key, a key where the short and full forms are the same, so a fixture hid the bug: a test of a path rule needs a value that tells the two rules apart. A ticket's "in Chromium" Done when reached main with no browser test, and nothing noticed.
- **Decisions affected:** none. A card that changes the card page can't picture its own panel in round 1, since the pictures are taken before its sheet exists; from round 2 on it can, half-drawn, as its After is being taken.

### F186 (2026-11-04): a sign-off stays signed ([review](../reviews/f186-why-can-t-i-sign-off.md))

- **Q1:** one lead ticket, merged first time; no checkpoint. Review round 1: one blocking, two should-fix and one nit fixed by the review, one nit only reported. Round 2: one should-fix in round 1's own fix, fixed there. Round 3: nothing new.
- **Q3:** no developer work (protected runner code). Sonnet built it for $0.33 and missed the half of D1 inside the review loop.
- **Q5:** see the review's numbers.
- **Anything else:** the ticket's test replaced the review with a stub, and the review was what set the milestone back, though the Done when asked for the status to stay. A race needs a test through the real path, with the other event in the middle of it. A heal that starts from open items can't see a wrong row with no item. A fault in the owner's own button waited over five days for its turn on the board.
- **Decisions affected:** none.

### F187 (2026-11-04): every time stored in UTC, shown in local time ([review](../reviews/f187-store-every-time-in-utc-the.md))

- **Q1:** three tickets: one developer ticket escalated after three failed attempts and finished by the lead on its branch, two lead tickets merged first time; no checkpoint. Review round 1: four should-fix and one nit fixed by the review, two nits only reported. Round 2: no fix merges, the fixes hold, nothing new.
- **Q3:** Qwen 0/3 on f187-02 (34 minutes, nothing merged). Sonnet passed f187-01 and f187-03 first time; its misses were all outside the ticket's lists.
- **Q5:** see the review's numbers.
- **Anything else:** UK winter hides this whole class of bug: both reset-time bugs passed here today and would have appeared on 28 March, and only a test with the zone set elsewhere shows them. Changing what a clock returns changes its readers as well as its writers, so a plan's list of writers isn't enough. A sweep by column name misses a value under another name (the Timeline's `bar.start`). The conversion of the old rows was still owed when the review stopped, waiting for the next backup, so the review checked it on tests only.
- **Decisions affected:** none.

### F203 (2026-11-04): a sign-off pushes the milestone to GitHub, and the bar says so ([review](../reviews/f203-push-to-github-at-sign-off.md))

- **Q1:** one lead ticket reviewed (f203-03), three lines of code and one test. Two attempts failed when Claude's login expired, and the ticket was blocked; the lead finished it from its branch in the owner's terminal session. No checkpoint. Review round 1: no defect, two nits only reported. The push itself (f203-01, f203-02) was built in a terminal session and wasn't in this review.
- **Q3:** no developer work (protected runner code). Neither Sonnet nor Opus could be judged: the login ran out under them.
- **Q5:** see the review's numbers.
- **Anything else:** an expired login looks like a passing error, so each job waited through its retries and then failed: about 3 hours of failed jobs, then about 7 with nothing running, for a three-line ticket. The block read "check-all failed", which pointed at the code. A terminal finish leaves no job row, so the metrics hold two attempts where the ticket says three.
- **Decisions affected:** none. bug-59 holds Claude's jobs and asks the owner to log in.

### F162 (2026-11-04): no checkpoint on merges the milestone's review is about to read ([review](../reviews/f162-doing-a-checkpoint-just-before-a.md))

- **Q1:** one lead ticket (f162-01), which merged on its second attempt: the first died with the expired login. No checkpoint. Review round 1: one blocking and four should-fix on the milestone, one should-fix on older code, two nits only reported. The review fixed the six itself, as `runner/` is protected.
- **Q3:** no developer work. Sonnet built what the ticket and ADR 38 asked for, for $0.81. The blocking bug came from the ADR's own reading of `restart`, so the ticket passed on that bug.
- **Q5:** see the review's numbers.
- **Anything else:** the ADR and the plan assumed a review's fix tickets wait under `restart`, but `restart` only means the runner's code changed. Fixes normally merge inside the review's loop with no stop recorded, so the milestone looked "due" and its last round's fixes were dropped with a log line saying the review would read them. An ADR's words about a state are worth checking against the code that sets it, at plan time. One test's comment also claimed a state it never reached, and it passed for the wrong reason: a test's setup should assert the state it says it reaches.
- **Decisions affected:** none. ADR 38's wording on `restart` is inexact, and the review report says so.

### F192 (2026-11-05): a fast lane request shows on the board and the Overview as soon as it's made ([review](../reviews/f192-when-i-click-use-the-fast.md))

- **Q1:** three developer tickets: f192-01 on its last attempt after a direction, f192-02 on its second attempt after a timeout, f192-03 escalated and finished by the lead. One checkpoint, on f192-01 only. Review round 1: three blocking, four should-fix and one nit, all fixed by the review except one should-fix set aside as bug-60.
- **Q3:** Qwen merged 2 of 3 developer tickets, none on its first attempt; about 3.9 of its 4.8 hours went to attempts that merged nothing. f192-03's lane logic needed the lead.
- **Q5:** see the review's numbers.
- **Anything else:** f192-02's gates were green on a blank field: on a phone, back emptied the board. Its test ignored the ticket's "second body" and used `count()`, which can't see a hidden column. "Fail without the change" isn't enough when the test only proves that some fetch happened: a redraw's test has to show the new thing, visible, at the width the owner uses. The ticket itself also dropped half of D3 (back without the browser's memory) from its Done when, so a developer who met every line would still have missed it: a ticket's Done when has to carry each branch of the decision it cites.
- **Decisions affected:** none.

### F219 (2026-11-05): lead tickets follow Claude's week pace, and the runner and dry run share one rule ([review](../reviews/f219-lead-tickets-don-t-wait-on.md))

- **Q1:** two lead tickets, both first attempts, no checkpoint. Review round 1: five should-fix and three nits; three fixed by the review, one fix ticket (f219-03), two set aside (bug-61, bug-62), two only reported.
- **Q3:** no developer tickets: `runner/` and the ADRs are protected.
- **Q5:** see the review's numbers.
- **Anything else:** removing the park at the reserve was tested thoroughly at the pick, but the review's rounds and `softfield milestone` also relied on a held ticket being parked. When a change removes a state, search for what reads the absence of work as well as what reads the state. The new rule also holds f9-29, the ticket meant to show it on the Overview, so a plan that counts on another card's ticket should say what happens if the rule holds that ticket.
- **Decisions affected:** none. ADR 44 stands.

### F171 (2026-11-05): each card once on the board, and fix tickets named after what they fix ([review](../reviews/f171-there-are-dupliacted-tickets-on-the.md))

- **Q1:** five tickets: two by the local model, each passing on its second attempt, and three by the lead. Two checkpoints: Copilot's stand-in filed one should-fix, which `f171-05` fixed; Claude's second found nothing. Review round 1: one should-fix and four nits; two fixed by the review, three only reported.
- **Q3:** the local model's two small dashboard tickets took 1.46 hours, 0.34 of it in failed attempts.
- **Q5:** see the review's numbers.
- **Anything else:** two tests written by the local model could never fail, because they looked for `F99` among rows keyed `f99-empty`, and the checkpoint called them sound. "Fails without the change" is written in every ticket's Done when, but nothing runs it. `f171-04` also waited 13 days after its card's other tickets had merged.
- **Decisions affected:** none.

### F188 (2026-11-05): the count leaves the review's phone bar ([review](../reviews/f188-i-don-t-need-the-4agreef.md))

- **Q1:** one developer ticket at difficulty 1 (one CSS rule, one test), Qwen first time in 35 minutes; no checkpoint. Review round 1: two should-fix and one nit, all fixed by the review.
- **Q3:** Qwen 1/1, no failed attempt. Opus $0.87 for the plan.
- **Q5:** see the review's numbers.
- **Anything else:** the ticket said "leave the template as it is" and the developer added an empty spacer to it anyway; the runner's "changed files outside `files:`" note flagged it, but no checkpoint ran. A Done when about the side not changed ("the count still updates on a wide screen") got no test: the developer tests what changes and skips what must stay.
- **Decisions affected:** none.

### F9 (2026-11-10): line polish ([review](../reviews/f9-line-polish.md))

- **Q1:** the longest-lived card so far: planned 2026-10-04, its last lead tickets (f9-29, f9-27) built 2026-11-10. About 28 developer tickets, nine of them fix tickets from 36 checkpoint findings; three lead tickets (f9-01 Opus, f9-29 and f9-27 Sonnet, all first time); three Opus escalations (f9-08, f9-30, f9-25). Review round 1: one should-fix the checkpoints missed (the Milestones page sorted not-started cards by key; fixed by the review), two nits fixed, two test-only fix tickets (f9-35, f9-36).
- **Q3:** Qwen about 34 hours of model, 13 of them in failed or timed-out attempts; see the review's numbers for dollars.
- **Q5:** see the review's numbers.
- **Anything else:** the checkpoints did their job on this card: all 36 findings were real, and the chains they started (phone title ×3, phone belts ×3) were each about placement on a phone or the floor's SVG, F3's lesson again. The one real bug no checkpoint caught was a sort whose test cases also sorted by key: a test that can't tell the right rule from a wrong one passes review by eye.
- **Decisions affected:** none.

### F169 (2026-11-10): the planner searches and reads the web ([review](../reviews/f169-why-is-web-search-related-tool.md))

- **Q1:** one lead ticket (f169-01, Sonnet, first time in 5 minutes, $0.26), no checkpoint. Review round 1: one blocking security finding (`git diff --no-index` read past the scoped reads), one should-fix on the tests, both fixed by the review; the `claude -p` probe ADR 33 asked for first was not run and is now the owner's sign-off check.
- **Q3:** Opus $0.66 for the plan, Sonnet $0.26 for the build.
- **Q5:** see the review's numbers.
- **Anything else:** a security ticket scoped one door (the Read tool) and left the command list open: when a job's reach is narrowed, the review has to check every tool it keeps, not only the one the ticket names. A ticket whose first step can't run in a job (a `claude -p` probe) should say so and hand that step to the owner's sign-off from the start.
- **Decisions affected:** ADR 33 gains a "Settled" line: no `git diff` beside the web.

### F61 (2026-11-11): Claude's meters say when the window runs out at this rate ([review](../reviews/f61-on-claude-usage-page-there-is.md))

- **Q1:** one developer ticket at difficulty 3 (a pure function, a template line, a legend line). Qwen 1/3: attempts 1 and 2 stopped "no edit after 20 min" (only reads), a 4-hour park for Claude's reset, then the third attempt passed the gates after an Opus direction ($0.47). No checkpoint. Review round 1: two blocking (the ghost's width from a true/false, the "before the reset" words garbled past 24 h) and two should-fix (loose tests, styling), all fixed by the review.
- **Q3:** Qwen 7.7M tokens in over three attempts, 75 minutes on the one that passed; see the review's numbers for dollars.
- **Q5:** see the review's numbers.
- **Anything else:** the gates trusted tests the developer wrote to match its own code: "the line contains 'at this rate: out'" passed a line with no gap and a negative one. When a ticket's Done-when quotes exact words, its tests list should quote the assertions too.
- **Decisions affected:** none.

### F77 (2026-11-11): allowance bars the same length, the same colours on every page ([review](../reviews/f77-the-bars-in-the-agent-allowance.md))

- **Q1:** two developer tickets. f77-01 (CSS grid, difficulty 2): Qwen 0/3 (two "no edit after 20 min", then `tests-fail-on-main` because its test drew bars already equal on main), parked about 9 h for Claude's reset, then an Opus direction and finish ($1.25). f77-02 (one Jinja macro, difficulty 3): Qwen passed on attempt 2 after a 79-minute timeout, no Claude. No checkpoint. Review round 1: one should-fix (f77-02's Done-when readings untested), fixed by the review; two nits reported.
- **Q3:** Opus $1.25 on f77-01; Qwen about 6.6M tokens in over both tickets; see the review's numbers.
- **Q5:** see the review's numbers.
- **Anything else:** for the second milestone running (F61, then F77), the gates passed a developer ticket whose Done-when readings had no test: "fail without the change" was met by re-spaced regexes. It recurs, so it should become a check. The ticket's own cause was also wrong (the lever, not the Fast lane line), which cost f77-01 its three attempts.
- **Decisions affected:** none.

### F206 (2026-11-11): the developer's view counts started tickets ([review](../reviews/f206-developer-is-curre-tly-working-on.md))

- **Q1:** one developer ticket at difficulty 3 (`_dev_work`, `dev_tag`, the legend). Qwen merged it on attempt 2 (the first failed its own tests): 73 min of model time and about 6M tokens in. No checkpoint. Review round 1: one blocking finding (handed-on cards lit, against D3, and counted on the Planted head), two should-fix (`then` ignored handed-on tickets; the handed-on words hid a lit card's work) and one nit, all fixed by the review. One nit was reported only.
- **Q3:** no Claude in the build; see the review's numbers.
- **Q5:** see the review's numbers.
- **Anything else:** this is the third milestone running (F61, F77, F206) where the gates passed tests the developer wrote to match its own misreading. Here the docstrings said "is faded" and the assertions said `dev-can`. One test for a Done-when line set up a different case from the one the line describes. A later card's test (F209) was then built on the wrong behaviour and had to change with the fix. The fix that keeps working is the review reading each test against the card's decisions. A cheap gate can't compare a docstring with an assertion.
- **Decisions affected:** none.

### F220 (2026-11-12): the project picker leaves inner pages for the lit tab ([review](../reviews/f220-if-i-m-browsing-a-certain.md))

- **Q1:** one developer ticket at difficulty 1 (one `action` on the picker's form, one `picker_to` on the Milestones list). Qwen merged it on attempt 1: 21 min of model time, 14 min of gates, about 3.6M tokens in. No checkpoint. Review round 1: one nit (a ticket's page missing from the parametrised test), reported only. Score 9.
- **Q3:** no Claude in the build; see the review's numbers.
- **Q5:** see the review's numbers.
- **Anything else:** a card whose plan read the code and named what each page did wrong, plus a ticket that gave the test's shape (find the form by its select, D3), gave a clean first attempt. The session report flagged the ticket as "edited existing tests" though it only appended one; telling appended from changed tests would spare reviews a false lead.
- **Decisions affected:** none.

### F226 (2026-11-12): the ⋯ menu drops "Open the card" ([review](../reviews/f226-the-open-card-s-from-the.md))

- **Q1:** one developer ticket at difficulty 1 (one template macro, two named tests edited as the ticket listed). Qwen merged it on attempt 1: 18 min of model time, 8 min of gates, about 0.9M tokens in. No checkpoint. Review round 1: two nits, reported only. Score 9.
- **Q3:** no Claude in the build beyond the planner ($0.92); see the review's numbers.
- **Q5:** see the review's numbers.
- **Anything else:** the ticket named the one trap (an empty `<template>` leaves white space that `:empty` doesn't hide), and the model avoided it. The before and after pictures show a page as it loads, so a change behind a tap (a menu, a dialog) shows nothing in them; this is worth a ticket if menu cards recur.
- **Decisions affected:** none.

### F227 (2026-11-12): the Queue panel drops "Reorder on the board" ([review](../reviews/f227-the-reorder-from-the-board-link.md))

- **Q1:** one developer ticket at difficulty 1 (one partial, four named test edits). Qwen merged it on attempt 1: 27 min of model time, 8 min of gates, about 1.5M tokens in. No checkpoint. Review round 1: one blocking (the count's branches swapped: "1 job waiting." with 143 tickets queued), fixed by Claude with two tests; one should-fix (the Done-when case untested), fixed with them; one nit reported. Score 6.
- **Q3:** no Claude in the build beyond the planner ($0.82); see the review's numbers.
- **Q5:** see the review's numbers.
- **Anything else:** green gates hid an unrequested change inside the block the model moved, because the tests it edited covered only what it removed. Comparing the before and after pictures caught it in seconds, where the after picture against the mock-up alone could have passed for "close". Keep comparing before against after in UI reviews; if this recurs, tell developers to change nothing else inside a block they move.
- **Decisions affected:** none.

### F230 (2026-11-12): Queue rows without a number use the whole row ([review](../reviews/f230-cards-in-the-queue-wrap-words.md))

- **Q1:** one developer ticket at difficulty 2 (a CSS grid rule, a template class, a browser test). Qwen merged it on attempt 3 (no-changes, then a timeout and a park for Claude's reset, then a directed pass): 37 min of model time, about 5.2M tokens in. A checkpoint re-checked it and raised nothing. Review round 1: three should-fix the checkpoint missed (`.count` deleted though still used, the stripe drawn over the label, a browser test of one Done when line out of three), all fixed by the review; one nit reported. Score 5.
- **Q3:** no Claude in the build beyond its direction; see the review's numbers.
- **Q5:** see the review's numbers.
- **Anything else:** "remove the unused rules" let the model remove a used one next to them: a ticket that deletes CSS should name each selector. The test covered the symptom the owner reported and none of the ticket's other lines, as in F188 and F77, so the bug those lines would have shown (text under the stripe) passed the gates.
- **Decisions affected:** none.

## 10. For the owner to decide at review time (each item can be accepted on its own)

1. 4.1: queue mode by default, and park the automated review loop.
2. 4.2 and 4.3: a separate factory repo, configured per project by `factory.toml`.
3. 4.4: FRONTIER.md plus pointer files.
4. 4.5: one report per milestone.
5. Whether to extract at all (Q7), and if so, when.
