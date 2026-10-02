# ADR 17: An always-on factory: Sonnet as the step-up, auto-format, tickets for later, milestones that wait, review fixes as tickets

- **Status:** Proposed
- **Date:** 2026-10-02
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 15](15-allowance-aware-routing.md) item 6 and [ADR 16](16-claude-window-and-named-milestones.md) item 2 (who develops); `docs/task-format.md` (a `later/` folder); `docs/workflow.md` (the review loop, gates); lead.md's Review
- **Evidence:** [`docs/reviews/f2.md`](../reviews/f2.md) and the metrics database (jobs 174–200); the owner's notes after F2 (`docs/roadmap.md`, "Owner's notes after F2").

## Context
- **The owner's first priority** (2026-10-02): the runner works on its own, takes any ready ticket as soon as it can, and can run a whole weekend unattended.
- **Sonnet as a developer competes with the lead.** Planning, reviews, escalations and lead tickets already fill Claude's 5-hour window.
  - The router gives a developer ticket to the best-rated permitted agent. With Claude idle, Sonnet (7) beats gpt-oss-120b (5), so the cloud developers get no work and no results.
  - Sonnet is still the best developer we have: 3/3 first time in F1, ≈$0.40 and 5–7 min a ticket.
- **gpt-oss-120b lost f2-06's five attempts to ruff alone**, in 0.4–2.3 min each: an unused import, undefined names, and lines over 100 characters. The prompt ends with `check-all --fix`; it never ran it.
- **No way to set a ticket aside.** `m4-12` and `f3-01` sat in `tasks/ready/`, where `runner run` would take them. The owner wants to park tickets and see them, to queue them again later. "Parked" already means "waiting for a limit" in the runner.
- **`runner run` already takes every ready ticket, in milestone order.** Nothing lets a milestone wait for the owner's sign-off of another.
- **F2's review took 21 min and $5.52** (128 steps, 12.7M cached tokens), and fixed five findings itself with tests: developer work at Opus prices.

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ Sonnet is the step-up, not a first developer** (amends ADR 16 item 2).
   - A developer ticket's first attempt never goes to Claude.
   - After a failed attempt, the step-up (ADR 15 item 7) may pick Sonnet only when no lead work is ready and Claude's 5-hour window is under **30%** (`developer_five_hour_cap`, down from 0.5). Otherwise the usual retry and direction follow.
   - Until the router has this rule, `claude-sonnet` is off `[roles] developer` (done 2026-10-02, for the weekend).
2. **⚑ The runner formats before the gates.**
   - After a developer attempt and before its gates, the runner runs `uv run ruff format` and `uv run ruff check --fix` on the Python files the branch changed, and commits the result into the attempt.
   - The ruff gate then judges what's left. It's deterministic and costs nothing, so a developer never loses an attempt to formatting alone.
3. **⚑ `tasks/later/`: tickets set aside** (amends `docs/task-format.md`).
   - The runner never takes a ticket from it, and records its tickets with the state `later`.
   - `uv run runner queue <ticket>` moves one to `ready/` and commits.
   - The dashboard lists them; a button follows with [ADR 18](18-dashboard-writes.md).
4. **⚑ A milestone can wait for another's sign-off.**
   - A milestone doc may say `After: <key> signed off`. Its tickets aren't picked until that milestone is done (`runner signoff`), and the verdict says what they wait for.
   - Without that line, milestones are independent, and `uv run runner run` (no key) is the standing command for unattended work.
5. **⚑ A review files its fixes as developer tickets** (amends lead.md's Review and `docs/workflow.md`'s review loop; the owner agreed the limits, 2026-10-02).
   - Every should-fix becomes a developer ticket, queued at once, with the finding's id.
   - **The review fixes it itself** when the fix is small (about 20 lines in one file), touches protected or security code, or a developer already failed that fix once.
   - Fix tickets get the usual checkpoint, not another review round; the review closes when they merge. The loop stays bounded by `review_rounds` and the third-return stop.

6. **⚑ Every ticket leaves main shippable** (owner, 2026-10-02; amends `docs/task-writing.md`). Milestones may be reprioritised and interleaved, so main can sit between two tickets of a feature for days.
   - A ticket either completes a usable slice, or adds code nobody can reach yet (no link, no route in the menu, no button). It never leaves something visible and half-working.
   - The lead plans for this, and each ticket's Done when says what a person sees after it, or "nothing visible yet".
   - No feature-flag system until a real case needs one.

**No ADR needed, bug fixes queued beside these:**
- After a yes to Claude's 5-hour window, parked work goes before the ticket that asked.
- A fresh Claude reading when a session starts.
- Pre-flight of a requeued ticket (f2-F4).
- OpenCode's shell timeout set by the runner, an operational timeout.

## Consequences
- Claude's window is kept for the lead and the owner; Ollama and local get the first attempts and their ratings move.
- A ticket can wait in `later/` without blocking a weekend run. A milestone that builds on an unsigned one can't run ahead of the owner.
- Reviews get cheaper; their fixes cost a developer attempt and a checkpoint instead.
- More Ollama use: its allowance is unmeasured (no API), so refusals are the only signal until a manual reading exists (ADR 18).

## Open questions
- **Does Sonnet come back at all?** Decide after F4's results (owner, 2026-10-02): as the step-up (f4-13), or off for good.
- Is 30% right for Sonnet's step-up? Revisit after a weekend's metrics.
- Should a review fix that blocks sign-off wait for its developer ticket, or be fixed at once? Default: wait, unless the owner signs off with it open.
