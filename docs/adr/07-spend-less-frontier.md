# ADR 07: Spend less of the Pro allowance on preparing work

- **Status:** Proposed
- **Date:** 2026-09-28
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

The owner asked whether the local model really saves their Claude Pro allowance: 9% of the week was used by the start of M3.

**The numbers for M3 so far** (`uv run runner status --milestone 3`, weighted by API price):

| | |
|---|---|
| Claude, from `m3-start` to the first runner session | ≈7.0M token-equivalents over 205 steps, ≈34k per step |
| Share spent re-reading the conversation | **84%** (average context ≈287k tokens per step) |
| Local model | 4 tasks, 476k tokens, free on the GPU; all 4 merged at the first attempt |
| Those 4 tasks done directly by Claude (≈5 steps each) | ≈0.7M, **about 10%** of what Claude spent |
| Preparing each delegated task | ≈8–10 steps: stub, failing tests, a throwaway reference implementation, spec, dry run, review |

**Conclusion.** For tasks this small, preparing them costs Claude more than doing them. And the biggest cost isn't the work at all: it's one very long session re-reading its own history at every step.

The M2 numbers point the same way, though they aren't weighted yet: 1.1M new tokens plus 53.7M cache reads for Claude, against 563k local tokens.

## Decisions

### 1. Short Claude sessions: one per phase

Each phase runs in its own fresh session, started with a short brief (`/clear`, or a new `claude`):
- plan and ADRs
- skeletons and tasks
- escalations
- review

The repo already holds the state (milestone doc, ADRs, tasks, runner reports), so nothing is lost. A step then costs roughly a context of 30–80k tokens instead of 290k: **3–5× cheaper**, whatever the step does.

This is a habit for the owner and Claude, not a rule the runner can enforce. Claude says when a phase ends and the next one should start fresh.

### 2. ⚑ No throwaway reference implementations

This changes the practice in `docs/task-writing.md` ("Before the task: the skeleton", item 4).

Claude no longer writes and deletes a working solution to check a task. Once written, it is the task; the local model then only repeats it.
- Claude still checks that the tests fail for the right reason, and runs pre-flight (`--dry-run`).
- `max_diff` is estimated, not measured.
- A spec error now shows up as a failed attempt and an escalation. Headless escalations are cheap: a short, fresh context.

### 3. ⚑ Fewer, bigger local tasks, and the local model writes tests for UI work

This changes `docs/task-format.md` (sizing) and CLAUDE.md ("write the failing tests yourself").
- **Size:** up to 3 files and about 150 changed lines. The M1–M3 evidence: 13/14 tasks passed at the first attempt on their final run, with most diffs under 60 lines. The model has headroom.
- **Low-risk UI tasks** (templates, CSS, copy, UI modules): Claude writes the goal, the context and the acceptance criteria as bullet points. The local model writes the tests and the code together.
- **Protected paths and security rules stay test-first by Claude.** Isolation tests, auth, crypto, the outbox and scoping are unchanged.
- A new gate checks that a task's `tests:` files exist and fail on `main` before the task's changes, so "the model wrote tests that always pass" is caught.

### 4. Sonnet for preparation, Opus for design and review

Mechanical preparation (stubs, specs from an agreed plan, dry runs) runs on Sonnet, which uses less allowance. Opus keeps the ADRs, protected code, security review and the milestone review. The owner switches with `/model`. Headless escalations use whatever `claude -p` defaults to (unchanged).

## Consequences

- **The report stays honest.** Since `ea166b7` it weighs tokens by price and compares against Claude's measured step cost. Each milestone review shows whether delegation paid.
- **More escalations at first:** specs aren't pre-proven any more. The headless cap (10 per milestone) stays; if escalations rise above about 2 per milestone, revisit item 2.
- **The local model's tests need a closer look at review:** Claude reads them the way it reads the French.
- **A gate change for item 3,** the "tests fail on main" check, with runner tests.
- **Measure after M4:** the M4 review compares weighted Claude spend per merged task against M3.
