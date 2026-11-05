# Milestone F192: A fast lane request shows on the board and Overview as soon as it's made

> **State:** done · **Priority:** 5 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-05. Base: git tag `f192-when-i-click-use-the-fast-start`. Report: [`.softfield/reviews/f192-when-i-click-use-the-fast.md`](../reviews/f192-when-i-click-use-the-fast.md).
> Planted by the owner on 2026-11-02.

## Notes
When I click use the fast lane and it's being queued for pick up, I want to see it already when I go back to the board

## Outcome
A fast lane lever pulled on a card's page shows at once on the board and the Overview, marked as on its way, until the runner takes it. Coming back with the phone's back button shows it too.

## Done when
- with a `reserve` request open for a planted card, the board's card says "fast lane · on its way · at the runner's next pick"; for one leaving, "leaving the fast lane · on its way"
- pressing back from the card's page to the board shows that plate without a reload
- the Overview's "Fast lane:" line and Next in line show the same, and go back to plain once the runner has taken it

## How to test
On a phone, on a planted card's page, pull the Fast lane lever and press back: the card on the board has the dashed plate. Open the Overview: the card is named, "on its way". After the runner's next pick, reload the board: the plain "fast lane" plate. Pull it off: "leaving the fast lane · on its way", then no plate.

## Today
`_reserve_lever` (`factory_dashboard/milestones.py`) reads the open `reserve` request for the lever alone. The board's plate, the Overview's line and Next in line read only the card doc's `**Fast lane:**`, which the runner writes at its next pick: F170's request of 30 October waited until 2 November, three and a half days with nothing on the board. Nothing on the board fetches again on the way back either, so a browser that restores the page from its memory would show it stale even with the plate built.

## Decisions
Mock-up: `.softfield/cards/f192-mockup/lane-on-its-way.html`.

- **D1: `Card.lane_asked: str | None`** in `factory_dashboard/board.py`: `"on"` or `"off"`, the latest open `reserve` request whose subject is the card's short key in lower case (as `_reserve_lever` finds it), only for a card in a `RESERVABLE` stage; else None. `_cards` reads all of them in one query, as it does `setting_aside`. `week` and `five_hour` are subjects too and match no card. Nothing is stored.
- **D2: the plate is its own mark.** `.card-reserve.on-its-way`, a dashed `--hazard` edge on the plate, not on the card: a card's dashed edge already means a reorder (F15 D4), and the two can be true together. It does not use `.card-way`, which `board.js` hides when the card is moved. A card with no open request keeps exactly today's `class="card-reserve"`.
- **D3: back shows what is true now.** `board.js` redraws the field on `pageshow` when the page came from the browser's memory (`event.persisted`) or by back or forward (navigation type `back_forward`), fetched past the browser's cache, by the same steps as after a send. With moves not sent, it leaves them alone and fetches nothing. No `Cache-Control` header: a header alone doesn't stop every browser restoring the page, and the moves not sent must survive.
- **D4: the Overview follows the request as the runner will.** The runner applies requests just before it picks (`apply_owner_requests`, then `_next_task`, `runner/loop.py`), so `reserve_marked` returns a card with `reserve` or `lane_asked == "on"`, and `_live_context` gives `fast_lane` those keys less any with `lane_asked == "off"`. Next in line is then right at once. The runner and the card's doc don't change.
- **D5: the board doesn't poll.** A card left open on the board keeps its plate until the next load, as a sent order does (F15 D4); polling would fight a drag.

## Tickets
| # | Ticket | Who | Diff. | After | What |
|---|--------|-----|-------|-------|------|
| 01 | board-plate-on-its-way | D | 3 | – | D1, D2: the plate |
| 02 | board-back-redraws | D | 4 | 01 | D3: back shows it |
| 03 | overview-lane-on-its-way | D | 4 | 01 | D4: the Overview's line and Next in line |
