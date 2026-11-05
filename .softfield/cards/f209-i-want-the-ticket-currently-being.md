# Milestone F209: The board lights the card at work and keeps itself up to date

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-03.

## Notes
i want the ticket currently being worked in the board be highlighted a bit more. also it doesn't seem to auto refresh very well

### From F218: Developer view if a developer is working on something, it… (merged by the lead on 2026-11-04)
Developer view if a developer is working on something, it should be highlighted as blue still. It currently doesn't even though it has the now tag

## Today (read in the code, 2026-11-03)
- **The card at work barely shows.** `started` gives every card with a ticket ever started the same orange edge: 16 of the 53 planted cards tonight. The card at work differs by one 12.5 px "Now:" line (`.card-now`), and it can sit far down the column: F9 is #23.
- **Only a ticket job shows.** `Card.running` comes from jobs with a ticket. A review has its small "Review running" box, and a planner job shows nothing beyond "the lead is answering", which comes from the thread, not the job.
- **The board doesn't refresh.** The page is drawn once. The 5 s poll in `base.html` updates the top bar only, so the bar can say a ticket runs while the board shows the last one. The field is redrawn only after a send, and the whole page reloads only when the dashboard's code changed (F38). That's why it sometimes looks fresh.

## Expected outcome
From the first screen of the board, on a phone too, you see what works now and on which card. The card itself stands out in its place in the line, and the board follows the work by itself within about 10 seconds.

## Done when
- With a job running, a plate above the plots names it, and its card has a thick frame and a filled "Working now" head, orange for the lead and blue for a developer, as the top bar's dot.
- When the ticket ends and the next starts, the plate, the card, the counts and the columns follow within about 10 seconds, with no tap.
- A drag, a ⋯ menu, moves not sent, a half-typed search or a scroll are never disturbed, and the plate says when moves hold the refresh.

## How to test
1. Open the board on your phone while a ticket runs: the plate is on the first screen, with the ticket and who works on it. Tap it: the card opens.
2. Press the plot of the card's stage and scroll to it: it is framed and filled, in its usual place.
3. Leave the page open past the end of a ticket: the plate, the card and the counts change by themselves.
4. Drag a card and don't send it: the plate says the refresh is held, your move stays. Send or cancel: the refresh is back.
5. Lock the phone for a while and come back: the board is up to date at once.

## Before and after
- `/board`

## Decisions
Mock-up: [`f209-mockup/working-now.html`](f209-mockup/working-now.html).

- **D1 At work means a live job on the card.** Any live job, whatever its role: a ticket's job on its card (a bug's on its own), a review's or a planner's on the card its `milestone` names, in any stage. `Card.at_work: Work | None` in `factory_dashboard/board.py`, the oldest live job. `Work` gains `who` (`lead` or `developer`, the same rule as `factory_status` in `factory_dashboard/app.py`: `job.role in DEVELOPER_ROLES`), `role`, `elapsed` and `waiting_clock`. A job whose run waits for Claude's limit isn't lit: its card keeps the frame without the fill, glow or lamp, and says until when.
- **D2 The colour says who works.** `.slot.at-work.lead` and `.developer` set `--who` to `--opus` and `--dev`, the top bar's dot. No new colour joins the tokens. The lamp breathes as the dot does, only without reduced motion. The card keeps its place: the board's order is the only order (owner, 2026-10-22). It keeps its growing tag. In the developer's view an at-work card keeps its frame at full strength, whatever it holds for developers (`dev-can`, `dev-waits` or `dev-none`): blue with a developer at work (F218's note), orange with the lead. Today that view ignores a ticket once it has started, so the card fades. Its words stay F206's, The board's developer's view counts tickets a developer has started.
- **D3 A plate at the top, always there.** `#board-now`, between the head and the plots, one row per live job of this project, each a link: a ticket's and a review's to the card, a planner's to its conversation. It ignores the search and the kind, and names the card's place (`#23 in Planted`) unless its stage isn't placed. With nothing at work, one quiet line, so the page doesn't move. `Board.now` holds what it draws, whatever `q` and `kind` keep. It's per project, as the board is (F132).
- **D4 The field fetches itself every 10 s.** `factory_dashboard/static/board.js` fetches `location.href` as a send does and compares the fresh `#board-now`, `#field .stages`, `#board-line` and each plot's count with what it last fetched. It swaps only what differs, so an unchanged board touches nothing and no animation restarts. It reuses the send's redraw: F192, A fast lane request's `f192-02-board-back-redraws` also makes one function of it, and whichever lands second uses it. 10 s and not the bar's 5 s: this fetches the whole page, and a ticket takes about an hour.
- **D5 What holds it.** No fetch while the page is hidden, and one at once on coming back. No fetch or swap during a drag, with moves not sent, with the ⋯ menu open, or while `window.liveIdle()` says no. A fresh page never reaches a drag begun during its fetch: the response is dropped. This replaces D5 of F192 ("the board doesn't poll: polling would fight a drag"): holding on those states answers it.
- **D6 It says when it's not fresh.** The plate's small line says "refreshes every 10 s"; "Refresh held: your moves aren't sent yet" with moves not sent; "Not updated since HH:MM: the dashboard doesn't answer" after a failed fetch, cleared by the next good one.

## Tickets
| # | Ticket | Who | Diff. | After | What |
|---|--------|-----|-------|-------|------|
| 01 | card-at-work | D | 4 | – | D1, D2: the card |
| 02 | plate-working-now | D | 3 | 01 | D3: the plate |
| 03 | field-refreshes-itself | D | 5 | 02 | D4–D6: the refresh |
