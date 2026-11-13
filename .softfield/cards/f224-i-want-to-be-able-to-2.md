# Milestone F224: Approve a plan to go first in line, in the fast lane

> **State:** done · **Priority:** 6 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-13. Base: git tag `f224-i-want-to-be-able-to-2-start`. Report: [`.softfield/reviews/f224-i-want-to-be-able-to-2.md`](../reviews/f224-i-want-to-be-able-to-2.md).
> Planted by the owner on 2026-11-05.

## Notes
I want to be able to approve a plan in high priority option. When approved this way, rather than going at the end of the queue (to go after the other thread that is refactoring the queue system) it will for first rather than last with fast lane on directly

## Expected outcome
On a review page, Approve first approves the plan, puts the card first on the board and turns its fast lane on, in one press. Approve plan stays as it is: last on the board, once F222, A newly approved plan goes last on the board, is built.

**The picture:** [`f224-mockup/approve-first.html`](f224-mockup/approve-first.html).

## Done when
- Approve first on a plan with tickets: at the runner's next pick the card is #1 in Planted with the fast lane plate, and its first ticket is next in line.
- Approve first twice, on two cards: the later press stands first.
- Approve plan on another card: it goes last and has no plate.
- Approve first on a replan: the card moves to #1 and the fast lane is on.
- Pulling the Fast lane lever off, or dragging the card, works as for any card.

## How to test it
On a phone, open a plan's review page, tap First…, read the words and press Approve first. Go back to the board: the card has the dashed "goes first" plate. After the runner's next pick, it is #1 in Planted with the plain "fast lane" plate.

## Decisions
- **D1: the request.** `approve_plan` with the value `first`; no value is a plain approval. `planner._about` already takes an approval of any value, so a proposal's state needs no change.
- **D2: one commit.** The card's state, its place and its mark go in the approval's commit, so a refused approval changes nothing. This is a press the owner could already make as three (approve, lever, drag), so it needs no ADR: it is the one exception to "what enters the line goes to the end" in ADR 45 item 3, and the fast lane's rules (ADR 35) stay as they are.
- **D3: what it takes.** Plan, mock-up and replan proposals, as Approve plan does. A replan's card moves first too: pressing it says so. ADRs, merges and seeds have no such button.
- **D4: no ticket, nothing goes first.** A card with no ticket in ready after the approval is approved as a plain one, and the result says so: only a planted card goes in the fast lane (F172 D2), and a lane card with nothing to run does nothing.
- **D5: a fold, as Reject… is.** Two taps, with the cost in words, because this one press can spend Claude's reserve and passes everything else. The phone's dock stays one row.
- **D6: shown at once.** An open request with `first` draws the dashed plate on the card in any stage, and the Overview's Fast lane line names it (the owner, 2026-10-07; F192 D4).
- **D7: built on F222.** It writes the same list as f222-01, so it waits for that ticket instead of writing the numbers first and again later.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | approve-first-in-the-runner | lead | 3 | f222-01 | D1–D4: the protected runner |
| 02 | approve-first-on-the-pages | developer | 3 | 01 | D3, D5, D6: the fold and the plates, after the mock-up |

## Before and after
- `/board`
- `/planning/f224/proposals/approve-first-plan`
