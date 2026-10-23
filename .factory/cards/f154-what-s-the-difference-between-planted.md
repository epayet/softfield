# Milestone F154: Each board stage says what it means and what moves a card on

> **State:** done · **Priority:** 2 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-23. Base: git tag `f154-what-s-the-difference-between-planted-start`. Report: [`.factory/reviews/f154-what-s-the-difference-between-planted.md`](../reviews/f154-what-s-the-difference-between-planted.md).
> Planted by the owner on 2026-10-20.

## Notes
What's the difference between planted and growing? I forgot and on mobile it's not very clear

## What we know (2026-10-20)
- `_milestone_stage` (`factory_dashboard/board.py`): **Planted** = plan approved, tickets in the queue, none started; **Growing** = at least one ticket started (running, done, blocked or escalated), until every ticket is done and the review's sheet is in (then Ripe). A bug ticket: ready → Planted, running or stopped → Growing.
- Growing doesn't mean "running now": the runner builds one ticket at a time, so of today's 12 growing cards only the one with a "Now:" line runs.
- On a phone (under 640 px) `dashboard.css` hides the board's explanation and the field's line, so the stage head's "tickets ready" or "in the factory" is all that is left, and the two sound alike.
- The runner already orders the board as one list: a `reorder` is every open card's key, first in line first (`_reorder` in `runner/requests.py`), with no stage in it. Only the dashboard splits Planted from Growing, and drags stay inside a stage, so a new planted card can't go before a growing one. The factory floor already counts them as one station ("planted plus growing", `factory_dashboard/line.py`).
- F152, A done card says where its review is (approved; f152-01 is ready), puts its review line on "growing" cards whose tickets are all done; after this card those are planted cards with work started, so f154-01 waits for f152-01 and keeps the line there.

## Settled with the owner
- 2026-10-20: Planted and Growing become one column, Planted, so any card can be dragged before any other; a card with work started says so on the card itself.

## Outcome
The board has one Planted column in the runner's order, any card can be moved anywhere in it, a card with work started shows it, and each stage says what it means and what comes next, on a phone as on a wide screen.

## Done when
- the board shows five stages (Seed, Sprouting, Planted, Ripe, Harvested); today's 26 planted and 12 growing cards are one Planted column of 38
- F151, I had to restart the runner, can be dragged above F106, Where do blocked tickets go, and sent
- F5, F106 and every card with a ticket started carry a "growing" tag and the orange edge; F151 doesn't
- the Planted head reads "in line for the factory, #1 first · 38, 12 growing" with "Next: every ticket done, then Claude reviews it" under it
- F106's page says "Stage Planted: in line for the factory · growing since" the day its first ticket started

## Decisions
- **D1. Five stages.** `STAGES` in `factory_dashboard/board.py` is seed, sprouting, planted, ripe, harvested. Where `_milestone_stage` and `_bug_stage` said growing they say planted, and `Card` gains `started: bool`: true for a milestone with a ticket started (`STARTED`, or a worked ticket), and for a bug running or stopped. `running` (the "Now:" line) is filled for any planted card with a live job.
- **D2. The words** (`WORDS` gains the next step; Harvested has none):
  - Seed: "an idea, or a ticket set aside" · Next: "a conversation with the lead plans it"
  - Sprouting: "being planned with the lead" · Next: "you approve the plan"
  - Planted: "in line for the factory, #1 first" · Next: "every ticket done, then Claude reviews it"; its head's count adds ", N growing" when N > 0
  - Ripe: "needs your sign-off" · Next: "you sign off"
  - Harvested: "signed off or fixed"
- **D3. A started card**: the class `started` on the card (the orange edge growing cards have today, `#stage-growing .card`) and a `card-growing` tag in its meta line, the growing plant and the word "growing", as the mock-up draws it (`.factory/cards/f154-mockup/stage-words.html`). Orange stays the colour that means work has started; the legend under the field says so.
- **D4. Everywhere a stage is read:** `factory_dashboard/static/board.js` (`PLACED`), `dashboard.css` (the growing rules and the phone order: Ripe, then Planted), `line.py` (the rows are the planted cards), `milestones.py` (`how_it_grew`: five steps, the started date on Planted as "growing since …"), `templates/milestone.html`, `templates/_partials/stage_icon.html` (the growing drawing stays, for the tag). The runner changes nothing.
- **D5. A lead ticket.** No protected path, but it changes a stage list three pages, a script and many tests read; a developer would likely miss one and the lead would finish it ("Who builds what").

## Tickets
- f154-01-stage-says-what-next (lead)
