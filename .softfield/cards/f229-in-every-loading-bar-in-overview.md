# Milestone F229: Remove the second bar with 4 chunks under every bar

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-12. Base: git tag `f229-in-every-loading-bar-in-overview-start`. Report: [`.softfield/reviews/f229-in-every-loading-bar-in-overview.md`](../reviews/f229-in-every-loading-bar-in-overview.md).
> Planted by the owner on 2026-11-05.

## Notes
In every loading bar in overview allowance planning and board number of tickets there is a second unnecessary loading bar under it with 4 chunks

From the code (2026-11-05): the strip is `.meter-ticks`, drawn after the `.meter` in `factory_dashboard/templates/_partials/allowance.html`, `factory_dashboard/templates/planning.html` (twice) and `factory_dashboard/templates/board.html`. F81, Bring the factory theme to the older pages, added it as quarter marks (f81-02, f81-08). It is a decoration: it shows no reading, and its pale chunks read as a second, empty bar.

## Plan
Mock-up: [`f229-mockup/meters.html`](f229-mockup/meters.html).
- **D1 The strip goes:** `.meter-ticks` leaves all three templates and `dashboard.css`, so each bar is one bar. Nothing replaces it: the percent is written beside each bar and the mark stays on it.
- **D2 The words keep their distance:** the strip was also the gap between the bar and the words under it, and the mark overhangs the bar by 4 px. A `.meter` gets `margin-bottom: 6px`, `0` on a board card, whose `gap` already spaces it.
- **D3 What doesn't change:** the bar's fill, colours and mark, the job page's bar (it never had a strip), and the Agents page's `.gauge`, which is a different thing.
- **D4 It stays gone:** a test holds that no template or stylesheet names `meter-ticks`. f219's mock-up still draws the strip and f9-29 builds from that picture; this keeps it from coming back whichever merges first.

| # | Ticket | Who | Difficulty | Waits for | What |
|---|---|---|---|---|---|
| 01 | no-strip-under-meters | developer | 1 | – | remove the strip and its rule, keep the gap, turn the old test around |

## Before and after
- `/`
- `/planning`
- `/board`
