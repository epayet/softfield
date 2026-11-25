# Milestone F296: Show each milestone's net code lines on its card in the…

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-25.

## Notes
Show each milestone's net code lines on its card in the board and on the milestone page beside its cost, so I can see which milestones grew the code without opening the review. From F286's review.

## What we know (2026-11-25)
- F286 (Reviews look for complexity and leave the code simpler) counts a milestone's code lines in `runner/report.py` (`_code_lines`): one `git show --numstat` per merged ticket (`Git.commit_code_lines`, `runner/gitops.py`), each time the report runs, for every milestone in its Trends. Nothing is stored (F286 D4, ADR 52 item 4); F286's review left "the report runs one git show per merged ticket of every milestone" as a nit.
- The metrics database keeps each merged ticket's commit and `lines_changed` (all files, tests included), written by `record_ticket` in `runner/session.py`.
- The dashboard has no git: it reads the database. The board is drawn on every visit and every 10 s refresh.
- Real numbers (code only): F286 +92 −13, F285 +216 −4, F273 +109 −2, F245 +2 −0; F290's eight merged tickets +6,170 −5,723.

## Outcome
Every milestone with a merged ticket shows its net code lines on its board card, in its page's "What it cost" line and in the Milestones table, from two numbers the runner keeps per ticket when it merges it.

## Done when
- a harvested card on the board shows a "Code +79 lines" plate (F286), and a planted card with merged tickets shows its net "so far"
- F286's page reads "$5.12, of which the review $1.35 · code +79 lines" on the closed "What it cost" fold, and "+92 −13, net +79" inside it
- the Milestones table has a "Code lines" column
- `softfield report` gives the same Code lines and Trends as before without running git

## Decisions
- **D1. Two numbers kept per ticket.** `tickets.code_added` and `tickets.code_removed` (a new schema step in `runner/metrics.py`), written by `record_ticket` beside `lines_changed` from `Git.commit_code_lines`, and by `runner/backfill.py` beside `commit_size`. `sync_tickets` fills them once for a merged ticket whose commit is set and whose `code_added` is NULL, so older milestones get theirs at the next run's start. This replaces F286 D4's "nothing stored" (ADR 52 item 4 says "computed from git each time"; the ticket adds "kept per ticket since F296" to it).
- **D2. Builds on and removes** (ADR 52 item 5): it builds on the ticket row and `commit_code_lines`; `_code_lines` in `runner/report.py` reads the columns and the report's `git` argument goes, with its per-ticket `git show`.
- **D3. One reader for the dashboard:** `code_lines(conn, project) -> dict[str, tuple[int, int]]` in `factory_dashboard/queries.py`, a milestone's full key to its merged tickets' (added, removed), one `GROUP BY` query; a milestone with no counted ticket isn't in it. The board, the milestone page and the Milestones table all read it.
- **D4. Net, in the rules' ink.** The board and the fold line show the net only ("+79 lines", "−40 lines"); the inside of the fold and nowhere else shows added and removed. No status colour: growing isn't a fault and shrinking isn't always good. A card with no merged ticket, and a bug card, show nothing.
- **D5. The picture is** `.softfield/cards/f296-mockup/code-lines.html` (Proposed; the calmer variant only if the owner asks).

## Before and after
- `/board`
- `/milestones/f286-i-want-code-reviews-to-highlight`
- `/milestones/f290-runner-loop-py-is-6-500`
- `/milestones`

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | code-lines-kept-per-ticket | lead | 3 | – | D1, D2 |
| 02 | code-lines-on-the-milestone-page | developer | 2 | 01 | D3, D4, D5 |
| 03 | code-lines-in-the-milestones-table | developer | 1 | 02 | D3, D4, D5 |
| 04 | code-plate-on-board-cards | developer | 2 | 02 | D3, D4, D5 |
