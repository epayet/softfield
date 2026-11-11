# Milestone F232: A plant waits 2 minutes before it becomes a card, so it can still be edited

> **State:** ready · **Priority:** 7 · **Area:** factory
> Planted by the owner on 2026-11-06.

## Notes
I can't edit a seed I just planted that has not been picked up yet anymore

## Why it happens
F14 lets the owner edit or cancel a plant from Coming seeds until the runner takes it, and the runner used to take plants only at its next pick, often half an hour later. Since F101 (the runner holds when idle) and f6-22 (the owner's pause), a runner with nothing to run applies the owner's requests every 5 seconds (`HOLD_POLL_S` in `runner/loop.py`). On 2026-11-06 the factory was idle, and F231, F232, F233 and F234 were taken 0.6 to 5 seconds after they were planted (`owner_requests` 1205 to 1211), so the editor never showed. While a ticket runs, a plant still waits for the next pick and can still be edited.

## Outcome
A plant from the Plant box can be edited or cancelled for at least two minutes after it is sent, whether the factory is busy, idle or paused.

## Done when
- planted while the factory is idle, an idea stays in Coming seeds, editable, for 2 minutes, then becomes a card
- an edit or a cancel made in those 2 minutes applies, as in F14
- its Coming row says when it will be planted ("planting in about 2 min"), then "planting at the runner's next pick" once the 2 minutes are over
- a seed planted from a review's idea (`subject` set, words are the lead's) and every other request go as they do today

## Decisions
- **D1. Hold the plant, don't edit the card.** `apply_requests` (`runner/requests.py`) leaves a plain plant (kind `plant`, no `subject`) open while it is younger than `PLANT_HOLD = timedelta(minutes=2)`, a constant in `runner/requests.py` that the dashboard imports. This brings back what F14 built. Editing a card's note after it is planted stays out (F90 D1): it would need a new request kind that rewrites a card doc and its title on main.
- **D2. Plants only.** A message on a thread (`plan_message`) is not held: a hold would add 2 minutes to every reply in a planning conversation.
- **D3. Changes still go first.** The hold only skips applying the plant. A `change` on a held plant is applied at once (cancelled, or new words), as `apply_requests` already does for changes.
- **D4. Quiet hold.** A held plant adds no line to the run's log each poll: the idle hold polls every 5 seconds.

## Tickets
- `f232-01-plants-wait-two-minutes` (lead: `runner/` is protected)
- `f232-02-coming-row-says-when` (developer)
