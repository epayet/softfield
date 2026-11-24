---
id: f97-03-a-lapsed-lever-asks-nothing
milestone: f97-given-that-the-planning-board-has
agent: lead
difficulty: 3
files:
  - runner/requests.py
  - runner/loop.py
  - .softfield/adr/22-one-visible-queue.md
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_loop.py
---

### Goal
When a "keep the board's order" lever's 24 hours end, it turns off quietly: there is no Needs-you item and no phone notification, and every open item from an earlier lapse is answered when the runner next starts.

### Context
Read `.softfield/cards/f97-given-that-the-planning-board-has.md` (D7).
- `_lapse` in `runner/requests.py` turns off a switch whose 24 hours are over (`loop.lapse_switches`). It then upserts an owner item of kind `loop.RESERVE_KIND` with the switch as subject ("Claude's reserve: … went off after 24 hours. Turn … on again for 24 h?") and notifies the phone. Keep the switch turning off and the returned line for the console. Drop the item and the notification.
- Since ADR 50 item 6 (`.softfield/adr/50-the-line-never-idles-for-the-pace.md`), a lever that is off only means lead tickets go after the developers' past the mark. Nothing waits for the owner, so the question asks for nothing. The Overview's allowance already shows each lever, on or off.
- Only a reserve request from the same project answers a lapse item (`_reserve` in `runner/requests.py`, around "the switch's own lapse item"). Two of travel-companion's, ids 195 and 196 from 2026-10-23, have stayed open for a month. Their stored words still say "use the week's reserve".
- `_resolve_reserve_parks` in `runner/loop.py`, called when a run starts (`_start_run`), answers the older parks and keeps "a lapsed switch's own item". Make it answer every open `reserve` item, the switches' too, and update its docstring and `RESERVE_KIND`'s comment.
- ADR 22's flagged note "A switch turned on lasts 24 hours" (`.softfield/adr/22-one-visible-queue.md`) says the runner asks again. Leave the note as it is and add one line under it: "No longer asks (owner, 2026-11-24, F97 D7): the lever turns off quietly."
- `test_a_switch_on_for_24_hours_reads_off_and_asks_to_be_turned_on_again` in `tests/runner/test_requests.py` checks the old ask: rework it to check that the switch reads off and that no item opens.

### Done when
- a switch on for more than 24 hours reads off, and no `reserve` owner item opens and no notification goes
- a run that starts with open `reserve` items whose subject is `week` or `five_hour` answers them; other projects' items are answered by their own run's start
- turning a switch on or off still works as before (`test_a_reserve_request_turns_its_switch_on_for_24_hours_and_off`)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
