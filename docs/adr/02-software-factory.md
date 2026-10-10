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
- **Anything else:** both features were already in real use before the review: a copy in `~/Dropbox/software-factory-backups` and five threads in `docs/planning/`. Reading the real exports showed the lead's points twice in each reply (text and boxes), which is the planner prompt's doing and already F41's fix. The review found no code defect; it added the restore steps (a backup nobody knows how to restore is half a backup) and one test.
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

## 10. For the owner to decide at review time (each item can be accepted on its own)

1. 4.1: queue mode by default, and park the automated review loop.
2. 4.2 and 4.3: a separate factory repo, configured per project by `factory.toml`.
3. 4.4: FRONTIER.md plus pointer files.
4. 4.5: one report per milestone.
5. Whether to extract at all (Q7), and if so, when.
