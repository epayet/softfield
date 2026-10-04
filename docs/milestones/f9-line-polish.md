# Milestone F9: line polish

> **Status: planned** (2026-10-04, with the owner). **State:** ready · **Priority:** 5 · **Area:** factory
> The owner's notes from using the line on 2026-10-04, plus three of f3-22's proposals they confirmed (f3-25, f3-28, f3-29, re-homed here with their ids). Developer tickets, each a small change on the lead-written line (F3's lesson: no SVG geometry for developers); 01 is the lead's.

## Outcome
- The floor shows when the line is clogged, and on what (a limit, the owner, a parked job).
- Light mode reads well: planted rows and the floor's yellow bars on grey.
- Planted rows open their milestone; seeds open the set-aside tickets.
- Idle machines look idle and say what they did today; plates show a bare one-decimal rating.
- Phone allowances are one row of dials.
- The Timeline's milestone filter works; the Set aside table shows each ticket's kind.

## Not here
- Crates moving along the belts (the F1 mock-up's motion) and a workflow page on the dashboard: `docs/roadmap.md`, after F8, since the crates should carry every kind of job.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | line-shows-waits | L | 4 | – | the floor shows a clog sign, with words, while the runner waits |
| 02 | light-floor | D | 2 | – | planted rows' words and the floor's bars readable in light mode |
| 03 | field-links | D | 3 | – | a planted row opens its milestone; the seeds open the Set aside panel |
| 04 | timeline-milestone-filter | D | 2 | – | the Timeline's milestone filter, "All milestones" included |
| 05 | later-kind-column | D | 2 | f5-09 | the Set aside table: Kind instead of the queue command |
| f3-25 | allowance-dials | D | 4 | – | (re-homed) phone allowances as dials |
| f3-28 | floor-words | D | 2 | – | (re-homed) bare one-decimal ratings, no "rated" |
| f3-29 | machine-today | D | 4 | – | (re-homed) idle machines say what they did today |
