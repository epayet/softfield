# Milestone F32: the 5 hour lead's window gauge on planning does'n say when it resets

> **State:** ready · **Priority:** 8 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
The owner, 2026-10-08: "the 5 hour lead's window gauge on planning does'n say when it resets".

From the code: the reset time is already worked out for every window (`reset_label` in `factory_dashboard/overview.py`, "resets at 17:00", the same words the Overview shows). The planning room's tile (`#lead-window` in `factory_dashboard/templates/planning.html`) only prints the percent, so this is a missing line, not missing data. Ticket f9-28 (ready, F9) is about to add a week row to the same tile, so this waits for it and covers both rows.

## Expected outcome
On `/planning`, the lead's window says when each of its windows resets, in the same words as the Overview, and says plainly when a reading is out of date instead of showing an empty bar with "–".

## Done when
- The 5-hour row reads e.g. "5-hour window 80% · resets at 17:00"; a reset on a later day reads "resets on Oct 9 12:00".
- The week row (from f9-28) carries its own reset the same way.
- With the reset already past and no newer reading, the row says "reset since, no new reading"; with no reading at all, "no data yet".

## Decisions
- **D1 Reuse the Overview's words.** `reset_label` and `status` from `agent_allowances`; no new wording, no countdown ("in 1 h 20") for now: a clock time stays true on a page left open, a countdown doesn't without a refresh.
- **D2 After f9-28.** Same tile, same files: building it first would make f9-28 conflict. The planning tile doesn't refresh itself (f9-28 makes only the Overview's panel live), so after a reset it keeps its old line until the page is reloaded; a clock time in the past reads as "already reset", which is acceptable.

## Tickets
1. `f32-01-lead-window-resets` (developer): each row of the planning room's lead window shows its reset or its status.
