# ADR 12: Juniors check their own work; checkpoints inside a milestone

- **Status:** Proposed
- **Date:** 2026-09-30
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

M4 was the first milestone run the ADR 07 way (tickets, not solutions; juniors write their own tests). From [`docs/reviews/m4.md`](../reviews/m4.md):
- **First-attempt pass rate: 5/9.** Escalations: 7, against a target of ≤ 3. Blocking findings in juniors' code: 1, against a target of 0. ADR 07's rule says to tighten, not to go back.
- **Gate failures the junior could have caught itself:** translations ×2 (m4-04) and ruff ×6 (m4-06). It has no command for the translations or layout checks, and the prompt asks it to run only its own tests.
- **Wasted attempts:**
  - 8 of m4-06's 9 attempts hit the 30-minute timeout
  - one attempt made 20+ near-identical edits without running a test
  - one ended without editing anything and passed every gate on an untouched tree, then crashed the merge
- **Silent failures in its tools:** piped commands (`| head`) are refused with empty output, and OpenCode's 2-minute shell limit cut off test runs whose failing tests each waited 30 s.
- **The review found problems the gates can't see, built on by later tickets:** m4-06 wired up m4-01 and m4-04's components before anyone had read them.
- **The lead also slipped:**
  - I committed type errors twice (`mypy | tail` hides the exit code)
  - a headless escalation committed one
  - I kept one lead session open through every phase, and the idle chat cost ≈10M of M4's ≈18M

## Decisions

### 1. ⚑ The junior runs every check it can
Amends `runner/prompts.py` (`LOCAL`) and `opencode.json`:
- **Allow** `uv run runner check-i18n` and `uv run runner check-layout`.
- **The finish line becomes:** `uv run ruff format …`, `uv run ruff check …`, `uv run mypy coucou tests runner`, `uv run runner check-i18n`, `uv run runner check-layout`, then the full `uv run pytest -q`.
- **The prompt says:** "Pipes, redirections and unknown flags are refused, and a refused command returns nothing. Run commands exactly as written."

### 2. ⚑ The runner cuts wasted attempts short
- **No changes, no gates.** An attempt that changes no file is a failed `no-changes` attempt, with a hint. *This is already in `main` (`7655448`) as a runner bug fix, since the alternative was a crash; this item asks the owner to confirm it.*
- **Loop stop.** If 8 steps in a row edit files without running a command, the runner stops the attempt and retries with the hint "you edited without testing; run the tests, then change one thing at a time". Steps are counted from OpenCode's JSON stream.
- **A timeout says so.** A retry after a timeout adds: "your previous attempt ran out of time. Keep what works and finish the smallest remaining piece first".
- **The timeout.** OpenCode's timeout is 2700 s (`runner.toml`, operational, changed during M4; noted here for the record).

### 3. ⚑ Pattern checks as a gate
A new `test-patterns` gate, placed after `layout`, flags these in the junior's added lines:
- `if … is_visible()` / `if … count()` branches in tests (a test that skips a step when something is missing passes without testing)
- `dispatchEvent(new Event('submit'…` or setting `.value` from JavaScript in UI tests (tests states a person can't reach)
- `time.sleep` / `wait_for_timeout` in browser tests
- a new module with no code in it

Each has a one-line hint. More are added only when a review finding recurs (lead.md already prefers checks to notes).

### 4. ⚑ Checkpoint reviews
- The plan marks **checkpoint tickets**: tickets that two or more others depend on, or that set a pattern others follow (`checkpoint: true` in the frontmatter).
- When a checkpoint ticket merges, the runner calls a short headless lead review of that diff **before its dependants run**.
- **The review does one of three things:** approve; write a fix ticket that the dependants then wait for; or tighten the dependants' tickets using what it saw.
- **Cost:** it counts against the existing cap of 10 headless runs per milestone. Nothing reaches the owner.
- **Trial:** M5 first. Keep it if checkpoint findings (plus the milestone review's) show fewer should-fix issues in juniors' code than M4's eight.

### 5. The lead's own discipline
Changes to `docs/agents/lead.md`, recorded here because they're what the numbers showed:
- **One fresh session per phase, really:** plan, own work, escalations, review. Don't keep a session open to watch a run. The runner reports when it's done, and the next phase starts from the repo.
- **One command before every commit to `main`:** a new `uv run runner check-all` (ruff, format, mypy, i18n, layout, the full suite) that fails on any error. Headless escalations use it too, before the runner commits their work. If it fails, the escalation is recorded as failed and no commit is made.
- **Read the junior's thinking** (OpenCode's `opencode.db`, `part` rows of type `reasoning`, read-only) at every escalation and review.
- **Plan depth:** keep junior dependency chains to at most three levels. Build foundations yourself (as with L0) when a chain would go deeper.

## Consequences
- **Juniors:** slightly longer finish lines, but fewer failed attempts on checks they can now run themselves.
- **Runner:** the loop stop and the pattern gate are the new code (a few dozen lines each, with runner tests).
- **Cost:** checkpoints add a few headless runs per milestone. They should pay for themselves by catching problems before other tickets build on them.
- **Measured at the M5 review, against M4:**
  - first-attempt pass rate (5/9)
  - escalations (7)
  - should-fix issues in juniors' code (8)
  - lead spend per junior task (≈2M)
  - timeouts (9)
