# Milestone F259: The Planning room's week bar shows Claude's pace, as the Overview does

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-17.

## Notes
The pace indicator is only on overview

From the code (2026-11-17): Claude's week bar is drawn in two places, the Overview's Agent allowance and the Planning room's "The lead's window" tile. Only the Overview passes the pace (`claude_pace` in `factory_dashboard/overview.py`) to `allowance_bar`; `planning` in `factory_dashboard/planning.py` passes none, so the tile shows "week 29%" while lead tickets are held over pace (22% today), with nothing saying so.

## Expected outcome
The Planning room's week bar shows Claude's week pace exactly as the Overview does: the dashed post, the striped stretch over it, and the same plate saying when lead tickets go on.

## Done when
- With the week over pace, `/planning` shows the post, the stripes and the "Over pace" plate with the same time and words as the Overview.
- On pace, the week's small line says "on pace · today's N%"; in the last hours, the "Last hours" plate shows; with the week's reserve lever on, neither.
- The Overview looks and reads as before.

## Decisions
- **D1 One macro for the plates.** The "Over pace" and "Last hours" plates move into `pace_plate(wp)` in `factory_dashboard/templates/_partials/allowance_bar.html`, called by the Overview and Planning, so the two pages can't say different things.
- **D2 Planning's words.** "on pace · today's N%" joins the week's small line; the plate goes under it. The 5-hour bar gets no post (pace is a week rule).
- Picture: [`.softfield/cards/f259-mockup/planning-week-pace.html`](f259-mockup/planning-week-pace.html).

## Before and after
- `/planning`
- `/`

## Tickets
1. `f259-01-planning-week-pace` (developer): the Planning room's week bar shows the pace post, stripes and plate, from one shared macro.
