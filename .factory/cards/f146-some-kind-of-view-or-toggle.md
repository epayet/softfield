# Milestone F146: The board's Developers only view: what runs without the lead, and for how long

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-16.

## Notes
Some kind of view or toggle in board to see developer only and developer only with 0 Claude allowance to see what's next in those scenarios would be helpful

The owner, 2026-10-27: "I want to see the board from a developer perspective. See what work can be done when only Devs are available"

The owner, 2026-10-28, sending back the first mock-up: "I rather imagined a toggle that would display the board from the perspective of a developer. It would hide any milestone that is just lead work or depends on a lead doing some work first or a checkpoint. Rather than completely hiding it could highlight milestones it can work on somehow compared to others. I might want to re prioritise some tickets based on that view so that needs to work there. I thought something like that rather than a section at the top"

## Where it stands (2026-10-28, from the queue)
- 80 tickets ready: 24 are the developers' (by the runner's rule, D1), 56 the lead's.
- Developers alone can work on 4 planted cards, 9 tickets: f59-01 (F59), f81-01 then f81-02 to f81-06 (F81), f82-01 (F82), f84-01 (F84). At the median 34 minutes a ticket, about 5 h 05 min; then every developer ticket left waits for the lead.
- 9 cards hold developer work that waits for a lead ticket: F15, F132, F42, F103, F62, F77, F89, F98, F170. f132-02-overview-live-every-project holds 6 of those tickets (F132's five and F62's one).
- No ticket waits for a checkpoint: a checkpoint only adds fix tickets, and comes before a card's review, which is Claude's anyway.

## Expected outcome
The board has a "developer's view" lever. Turned on, the same board shows which cards developers can work on (lit), which hold developer work that waits for the lead (half-dark, naming the lead ticket) and which are lead only (faded), each said in words on the card. Everything stays in its place and can be dragged and sent as from the normal view, so the owner can reorder with that picture in front of them.

## Done when
- `/board` has a "developer's view" lever after the kinds; it is a link to `?view=developers` and back, and search and the kinds keep it.
- In that view every planted card gets one line and its look:
  - **lit:** "developers: N now · M after it", then what follows ("then the lead's f81-07", "then Claude's review");
  - **half-dark:** "N developer tickets wait for f132-02" (the lead tickets named);
  - **faded:** "lead only".
- The other stages fade whole: their cards have no ticket to run.
- The Planted stage's head says how many cards and tickets developers can work on, and for about how long.
- Grips, ⋯ and Send new order work as in the normal view.
- On the queue of 2026-10-28 (above), the view says what "Where it stands" says.

## Decisions
- **D1 Who is a developer ticket: the runner's rule.** A ready ticket is the developers' when `runner.router.lead_only(kind, files, protected)` is false, with `protected` from `runner.config.read_protected(repo)` and `kind` and `files` from the `tickets` row. No checkout: `kind` alone. So a ticket with no `agent: lead` but files under `runner/` is the lead's, as the runner takes it.
- **D2 What developers alone can run.** A developer ticket whose every `depends_on` is done can start **now**; one whose every unfinished dependency is itself a developer ticket that can run comes **after** them (transitively). Every other developer ticket **waits for the lead**, naming the unfinished non-developer tickets it waits for, directly or through another developer ticket. A dependency that is set aside, blocked or unknown counts as waiting, under its own id.
- **D3 A card's look.** `can` when it has a ticket of D2's now or after; else `waits` when it has a developer ticket; else `none`. Only planted cards get one; every other stage shows `none`.
- **D4 The data lives in `factory_dashboard/board.py`:**
  - `DevWork`, a frozen dataclass on `Card` as `developers: DevWork | None` (None outside the view): `look` (`can`, `waits`, `none`), `now`, `after`, `waiting` (counts), `waits_for` (the lead tickets named, in id order), `then` (for a `can` card: the first lead ticket left in it, else `review` when all its not-done tickets are developers', else None).
  - `board(..., developers=False)` fills it; `Board.developers: tuple[int, int, float | None]` holds the cards and tickets of look `can` and the work's minutes (tickets times the median of `runner.loop.ticket_minutes`, None when it has no rows).
  - Nothing else in `board()` changes: the cards' order, places and `line` stay the same, so a reorder sent from this view is the same request as from the normal one.
- **D5 The view is a query parameter,** `view=developers`, beside `kind` and `q`; anything else is the normal board. It changes only looks and words, never which cards show or where.
- **D6 One lever, not two.** "No Claude at all" lists the same tickets as "developers only" (a developer ticket never needs Claude to start); what differs comes after, and the card's `then` says it.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | developer-line | L | 4 | – | D1–D4: `DevWork` on each card, and the stage's totals |
| 02 | developers-only-view | D | 3 | 01 | D5: the lever, the cards' looks and lines, after the mock-up |

The picture: `.factory/cards/f146-mockup/developers-only.html`.
