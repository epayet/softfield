# ADR 07: Lead and juniors: spend less of the frontier allowance

- **Status:** Accepted (by the owner, 2026-09-29)
- **Date:** 2026-09-28, rewritten 2026-09-29 after the owner and Claude reviewed it against the end of M3
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

The owner asked whether the local model really saves their Claude Pro allowance. By the end of M3 (`uv run runner status --milestone 3`, weighted by API price):

| | |
|---|---|
| Local model | 11 tasks, 10 at the first attempt, 1.3M tokens, free on the GPU |
| Claude, `m3-start` to sign-off | ≈19.5M token-equivalents over 699 steps (≈28k a step, 78% of it re-reading the conversation) |
| Those 11 tasks done directly by Claude | ≈1.5M (about 5 steps each), **8%** of what Claude spent |
| Preparing each delegated task | ≈8–10 steps: stub, failing tests, a throwaway reference implementation, a spec with every signature pasted, a dry run, a check after the merge |

**What that says:**
- **Handing a task off cost more than doing it.** The lead solved each task to hand it off, and the junior only re-typed the answer.
- **We over-prepared.** 10 of 11 tasks passed at the first attempt. The one failure, m3-12, came from the preparation itself: a `max_diff` of 90, estimated from a reference implementation, against about 95 real lines.
- **Most of Claude's spend is its own protected work** (auth, scoping, the stream, the outbox). Delegation can't touch that; shorter sessions can.

**The owner's framing:** the frontier model is the **tech lead**, and the local models are **junior engineers**. A lead who does the juniors' work saves nothing. Juniors need guidance, cheap deterministic checks and feedback, not solutions. The lead may not always be Claude ([ADR 02](02-software-factory.md), WIP), so the shared docs say "the lead", and Claude-only details stay in CLAUDE.md.

## Decisions

### 1. Short sessions, one per phase
Plan, tickets, the lead's own work, escalations and review each run in a fresh session, started from the repo's state (milestone doc, ADRs, tasks, reports). The lead says when a phase ends. Evidence: runner sessions ran at ≈16–20k a step after the M3 handoff (`0a71f09`), against ≈34k before.

### 2. ⚑ Tickets, not solutions
Changes `runner/instructions/task-writing.md` (the skeleton and the reference implementation) and CLAUDE.md ("paste every signature…; must never need to explore").
- A ticket is a goal, the files to read (paths, not pastes) and acceptance criteria as bullets. Paste only a fact no file holds.
- No throwaway reference implementation and no stubs for junior work.
- Budget: about 1–2 lead steps per ticket. A milestone's tickets are written in one pass.

### 3. ⚑ Worked examples, once per kind of task
The first task of a new kind (a new language, layer or pattern) is built by the lead and listed as the example in `runner/instructions/junior.md`. Later tickets say "follow X". This replaces per-task reference implementations.

### 4. ⚑ Juniors write and change tests
Changes `docs/testing.md` ("existing test files are immutable") and the gates.
- Juniors write the tests for their tickets, and may change existing tests when the behaviour changes.
- **Security stays test-first by the lead.** Protected code and the tests that guard it (listed in `.softfield/protected-paths.txt`) are the lead's.
- Two gates replace "existing tests unchanged":
  - `no-new-skips`: no added `skip`/`xfail`.
  - `tests-fail-on-main`: the test files a task added or changed must fail against main's code, so they test the change.
- The session report lists every existing test a junior changed, for the review to read first.

### 5. ⚑ Deterministic checks replace per-task review
- **Layout check** (`layout_problems` in `tests/browser/conftest.py`): at phone and display sizes, text and controls don't overlap or leave the screen sideways. It catches the kind of problem M3's screenshots found.
- **French tone check** (`tests/integration/test_french_tone.py`): no "Veuillez"-style formal phrasing. It came back twice in M3.
- When a review finding recurs, it becomes a check rather than a sentence in a spec.

### 6. ⚑ Feedback
- **In a task:** on a retry, each gate says what to do, not only what failed (`HINTS` in `runner/gates.py`).
- **Across tasks:** a lesson becomes a check first, a worked example second, and a line in `runner/instructions/junior.md` last.
- `junior.md` has a hard budget of **15 one-line notes**, because local models drop instructions from long prompts. When it's full, a line is replaced or becomes a check. The lead edits it without an ADR. Gates, caps and the task format still need one.

### 7. No per-task checks by the lead
The gates merge. The milestone review, which already reads the whole milestone's diff, also reads the tests for missing edge cases, reads every test a junior changed, and checks the French. Screenshots when the lead has a browser at hand.

### 8. ⚑ Size by concept, not lines
Changes `runner/instructions/task-format.md` and `.softfield/project.toml`.
- A task is **one concept**, touching as many files as it needs. The "1–3 files" guideline and per-task `max_diff` go.
- The only line limit is a very generous backstop of **1000 lines**, to catch a file rewritten from scratch (a timeout wouldn't: a rewrite takes minutes). Reassess at the M4 review.
- Evidence: max-diff fired 3 times in M1–M3, all false alarms on m3-12. The largest local diffs passed at the first attempt at 112 and 119 lines.
- **How the lead judges fit:**
  - no open design decisions in a ticket; the lead makes them and writes them in
  - is there a worked example to follow? If not, the lead builds the first one
  - how much the junior must read, since its context (about 180k tokens) is the real ceiling
  - a **known range** in `runner/instructions/lead.md`, updated at each milestone review from the results. The runner reports diff size, attempts and local tokens per task.

### 9. ⚑ `files:` is a pointer, not a gate
The `allowed-files` gate never fired in M1–M3 and is dropped. Tickets still say where to work, and the session report lists files changed outside `files:` and `tests:`. The hard limits stay: protected paths, no new skips, no new dependencies, all tests passing.

### 10. Stretch tickets
Some tickets deliberately go past the known range, to learn what the juniors can do. Their failures are logged and don't count against the targets below.

### 11. Models, as a nudge
The lead ends each phase with a ready-to-paste command for the next session, with a cheaper model where the work is mechanical (details in CLAUDE.md). The owner may ignore it; nothing depends on it. Headless runs keep the default.

### 12. What reaches the owner, and only this
- accepting ADRs: design, and workflow rules
- critical code decisions: security, privacy, data loss, and **changes to the overall code architecture** (layout, layers, big patterns)
- milestone sign-off and the real-device check

The lead decides everything else and records it in the review report. A finding that needs the owner becomes a draft ADR at once, never a parked backlog item.

### 13. A sign-off sheet at the end of every milestone
At the top of `.softfield/reviews/mN.md`, in plain language, written by the lead unasked when the review loop stops: what changed, how to test it yourself (numbered steps on real devices), what was left for later, decisions waiting for the owner, and how the work went (one line per session, the lessons that mattered, links to `.softfield/sessions/`). The message in the chat stays short: a link and 2–3 lines.

### 14. ⚑ Agent docs split by role, not by vendor
Changes AGENTS.md, CLAUDE.md and `opencode.json`.

| File | Read by | Holds |
|---|---|---|
| `AGENTS.md` | everyone; OpenCode loads it for juniors | Shared rules for anyone writing code here. Its first lines route each role. |
| `runner/instructions/junior.md` | juniors; OpenCode loads it too | The 15-line notes and the worked examples |
| `runner/instructions/lead.md` | any frontier lead | The process, the owner's standing preferences, the known range |
| `CLAUDE.md` | Claude only | "You are the lead", plus Claude-only details |

Owner preferences live in `lead.md`, not in a vendor's memory, so a different frontier inherits them.

### 15. Protected paths stay, and get trimmed where too broad
They do two jobs review can't: they keep juniors off the workflow (gates, runner, permissions, AGENTS.md), and they keep security code lead-written and test-first. But protected means expensive lead work, so at each milestone's plan the lead splits over-broad files where it can. For example, `display.js` wires the outbox and the stream, so all of ADR 09's history UI became lead work. Its UI could move to an unprotected module.

### 16. Decide the joints, not the insides

| Level | Who decides, when | Where |
|---|---|---|
| Architecture: layers, storage, big patterns | the owner, via an ADR | `.softfield/adr/` |
| Contracts between pieces: API shapes, data fields, module functions, file ownership, which example to follow | the lead, in the plan session | a short "Decisions" section in `.softfield/cards/mN.md` |
| Internals of one piece | the junior | the code, checked by tests, gates and review |

**The test:** "If the junior chose differently, would another ticket, the security model or stored data break?" If yes, decide it in the plan; if no, leave it to the junior. A long decisions list means an architecture change, which needs an ADR. The lead builds its own parts first, so juniors code against real contracts. A `BLOCKED.md` saying `false-assumption` or `needs-info` flags a wrong or missing decision.

## How a milestone runs now (M4, the sender app, as the example)

1. **Plan session:** the lead's list (e.g. the upload endpoint, the outbox, the isolation tests) and the juniors' list (e.g. the compose screen, preview, status list, send wiring, French, plus 1–2 stretch tickets). The Decisions section. An architecture change becomes an ADR for the owner.
2. **Ticket session:** all tickets in one pass.
3. **The lead's protected work,** test-first. At the same time the runner works through the tickets that don't need it, one at a time. A ticket that needs the lead's part is queued once that part is on main.
4. **Runner:** juniors write tests and code, and the gates decide.
5. **Milestone review loop** (automatic, headless): small findings become tickets, protected or quick ones are fixed by the lead, and a real decision becomes an ADR and stops the loop.
6. **Sign-off sheet** for the owner.

Per delegated task: M3 ≈10 lead steps; doing it directly ≈5; this ADR aims for ≈2.

## Considered and rejected
- **The lead doing small tasks directly.** Cheaper delegation keeps the learning about what local models can do.
- **A higher cap for CSS only.** Replaced by sizing by concept plus a backstop.
- **Sonnet for headless escalations.** They're rare (5 in M1–M3) and cheap, and the costly ones need judgement.

## Deferred
**More than one junior at a time.** LM Studio can queue parallel requests, but it's set to no parallel workers, and switching contexts may cost more than it saves. This needs a future ADR (noted in `docs/backlog.md`).

## Consequences and measures
- More escalations at first, because specs aren't pre-proven. The headless cap (10 per milestone) stays *(replaced by limits per trigger, [ADR 12](12-junior-feedback-and-checkpoints.md) item 10)*. More than about 3 escalations per milestone → tighten the tickets (examples, checks, lead-written tests), never go back to worked solutions.
- **Measured at the M4 review, against M3:**

| Measure | M3 | Target for M4 |
|---|---|---|
| Lead steps in the ticket session ÷ tickets | ≈10 per task | ≤ 2 |
| Share of the milestone's lines written by juniors | small | clearly higher |
| First-attempt pass rate | 10/11 | 60–80% |
| Escalations | 1 | ≤ 3 |
| Blocking findings in juniors' code | 0 | 0 |
| Lead spend per merged task | ≈1.8M | clearly lower |
| Lead cost per step | ≈28k | ≤ 20k |
| Escalations from missing or wrong decisions | – | counted |
| Lessons turned into checks | – | counted |
| Stretch tickets | – | logged |

- **Decision rule at M4's review:** keep and extend the approach if tickets cost ≤ 2 steps, the juniors' code has no blocking findings and escalations stay ≤ 3. Otherwise tighten, as above.
