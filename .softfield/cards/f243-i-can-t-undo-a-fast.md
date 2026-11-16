# Milestone F243: Pull a fast lane lever back before the runner takes it

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-13.

## Notes
I can't undo a fast lane trigger that hasn't been picked up by the runner yet

## Outcome
A fast lane lever pulled by mistake can be pulled back before the runner takes it. The lever goes back to how it was at once, the board and the Overview stop saying "on its way", and at its next pick the runner changes nothing and commits nothing. The two "use reserve" levers on the Overview's allowance work the same way.

## Done when
- on a planted card's page, pulling the Fast lane lever shows it on its way; pulling it again puts it back as it was, plain, and it can be pulled a third time
- the board's plate and the Overview's "Fast lane:" line follow the latest pull: none after a pull-back
- at the runner's next pick, a pull and its pull-back leave the card's doc as it was, with no commit, and the requests read "taken back"
- a "use reserve" lever pulled and pulled back leaves its switch as it was

## How to test
On the phone, open a planted card not in the fast lane (F199, The factory floor). Pull Fast lane: dashed edge, knob halfway. Pull it again: plain, off. Go back to the board: no plate. After the runner's next pick, `git log` on main has no "in the fast lane, by the owner" commit for it. Do the same with a card already in the lane: it stays in.

## Today
The lever is `disabled` while its request is open (`factory_dashboard/templates/milestone.html`, and the same on `_partials/allowance.html`), so a pull can't be taken back. A request waits for the runner's next pick, which can be most of an hour away (F192's waited three and a half days). Pulling twice wouldn't help anyway: the runner applies every open `reserve` request in order (`apply_requests`, `runner/requests.py`), so "on" then "off" would make two commits on main.

## Decisions
Mock-up: `.softfield/cards/f243-mockup/take-back.html`.

- **D1: the latest pull is the owner's word.** In `apply_requests` and `take_switches` (`runner/requests.py`), for each `reserve` subject only the latest open request is applied; an earlier one still open finishes as `REPLACED`, as an older board order does (F15 D4). The latest, when it asks for what is already so (the card marked or not, the switch on or off), finishes as "taken back: F199 stays out of the fast lane" (or "stays in", or the switch's words) and commits nothing. No new request kind: a take-back is a `reserve` request whose value is the state as it stands.
- **D2: an open request no longer locks the lever.** `ReserveLever.asked` (`factory_dashboard/milestones.py`) and `Switch.asked` (`factory_dashboard/overview.py`) are the latest open request's value only when it differs from the state as it stands; else None, and the lever is drawn plain. The lever is never `disabled` by a request. Each pull flips it in place: plain → on its way (sends the other value) → plain (sends the value as it stands) → on its way. The `title` says "pull again to take it back" while on its way. Nothing else on the lever changes.
- **D3: the plates follow the same rule.** `Card.lane_asked` (`factory_dashboard/board.py`) is None when the latest open request asks for what the card already is, so the board's plate, the Overview's "Fast lane:" line and Next in line show nothing on its way after a pull-back (F192 D1, D4 otherwise unchanged).
- **D4: Approve first can't be taken back here.** A plan approved with "goes first" (F224) is an approval, not a lever pull; once it lands, the card is in the lane and its lever pulls it out. Unchanged.

## Before and after
- `/milestones/f199-let-s-improve-the-factory-floor`
- `/board`
- `/`

## Tickets
| # | Ticket | Who | Diff. | After | What |
|---|--------|-----|-------|-------|------|
| 01 | latest-lane-pull-wins | L | 3 | – | D1: the runner applies only the latest pull |
| 02 | lever-pulls-back | D | 3 | 01 | D2: the levers can be pulled back |
| 03 | plate-follows-pull-back | D | 2 | 01 | D3: the board and the Overview |
