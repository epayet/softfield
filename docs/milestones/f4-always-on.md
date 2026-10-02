# Milestone F4: always on

> **Status: planned** (2026-10-02). From the owner's notes after F2 (`docs/roadmap.md`, "Owner's notes after F2"). The owner's priority 1: the runner works on its own and takes any ready ticket, for a weekend unattended. [ADR 17](../adr/17-always-on-factory.md) must be Accepted before tickets 09, 11, 13, 15 and 18 run; if it isn't, they wait in `tasks/later/`.
> Numbered F4 because F3 (the factory line) keeps its key: `f3-01` has a half-done branch and a saved session under that id.

## Outcome
- The runner can be left on with `uv run runner run`. Claude's work waits for room while developer tickets keep going, and a yes to Claude's reserve releases parked work first.
- Developers lose no attempt to formatting, and Sonnet only steps in after a failure.
- Tickets can wait in `tasks/later/`, and a milestone can wait for another's sign-off.
- The Overview answers "what is it doing, for which goal, and what waits for what" without a reload:
  - allowances at the top;
  - the queue beside Running now, in run order;
  - no lost text selection.
- The Tickets page shows the latest work first.

## How to run it (the owner)
1. Accept ADR 17 (`uv run runner accept 17`), or say no, and the lead moves 09, 11, 13, 15 and 18 to `tasks/later/`.
2. Optional, first: the bench (`docs/roadmap.md`, "Cloud workers"):
   ```
   uv run runner bench f1-38-project-page-fixes m4-11-send-once --agents ollama-gpt-oss-120b ollama-gemma4-31b ollama-nemotron-3-ultra
   ```
3. `uv run runner run`.

## Decisions
- **D1 Sonnet off `[roles] developer`** from 2026-10-02 (ADR 17 item 1). Ticket 13 brings it back as the step-up only.
- **D2 Interleaved numbering.**
  - Lead and developer tickets alternate, and the lead tickets are independent of each other.
  - When Claude parks, a developer ticket is always ready.
  - The developer tickets on the Overview form one chain (08 → 10 → 12 → 14, 16), because they share `factory_dashboard/templates/overview.html`.
- **D3 What a queued ticket waits for** (08). It is computed in `factory_dashboard/overview.py` from the `tickets` table:
  - a `depends_on` ticket not `done` ("waits for f4-08-…");
  - an escalated one ("waits for f4-08-…'s escalation");
  - a lead ticket while a live run's `activity` starts with "waiting for Claude" ("waits for Claude").
  - The order is `pick_next`'s rule (`runner/tasks.py`): milestone order, then id, with tickets whose dependencies are done first.
- **D4 The `later` state** (09): `tasks/later/` is synced into `tickets.state = 'later'`, and the dashboard's later list (18) reads that.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | yes-resumes-parked | L | 4 | – | After a yes to the 5-hour question, parked escalations and checkpoints go before the ticket that asked |
| 02 | tickets-last-worked | D | 2 | – | Tickets page: latest work first, with a "last worked" column |
| 03 | requeue-preflight | L | 4 | – | A requeued ticket is pre-flighted before it's committed (f2-F4) |
| 04 | running-goal | D | 3 | – | Running now and the wait line show the ticket's goal |
| 05 | opencode-shell-timeout | L | 3 | – | The runner sets OpenCode's shell timeout, so `check-all` isn't killed at 120 s |
| 06 | running-tokens | D | 2 | 04 | "read N tokens · M turns", cached input included |
| 07 | fresh-reading | L | 4 | – | A fresh Claude reading when a session starts |
| 08 | queue-waits-for | D | 4 | – | The queue leaves out running tickets, follows run order and says what each waits for |
| 09 | later-folder | L | 5 | – | `tasks/later/` and `runner queue <ticket>` (ADR 17 item 3) |
| 10 | queue-live | D | 4 | 08 | The queue refreshes with Running now, beside it, with a height limit |
| 11 | auto-format | L | 4 | – | `ruff format` and `ruff check --fix` before the gates (ADR 17 item 2) |
| 12 | allowance-top | D | 3 | 10 | Allowances at the top of the Overview, refreshed every 5 s |
| 13 | sonnet-step-up | L | 4 | – | In `tasks/later/`: Sonnet only as the step-up, under 30% (ADR 17 item 1), if F4's results say it should come back |
| 14 | keep-selection | D | 2 | 12 | No refresh while text is selected |
| 15 | milestone-after | L | 5 | – | `After: <key> signed off` in a milestone doc (ADR 17 item 4) |
| 16 | allowance-mark | D | 2 | 12 | The reserve marks visible in both themes |
| 17 | agents-model-label | D | 2 | – | "not recorded" says why |
| 18 | later-list | D | 3 | 09 | The Tickets page lists the tickets set aside |

Not in F4 (roadmap, "Owner's notes after F2"):
- a study of why `check-all` is slow (later, a proposal, not a fix);
- ADR 18 (dashboard writes) and ADR 19 (feature board), drafted for the next planning session.
