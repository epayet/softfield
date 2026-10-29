# Milestone F77: Allowance bars: the same length on the Overview, the same colours on every page

> **State:** ready · **Priority:** 4 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
the bars in the agent allowance are not the same size

The owner, 2026-10-26: "And the colors are different between pages".

From the code (2026-10-26):
- **Sizes.** The Overview's `#allowance` lays its windows out as a wrapping flex row (`.allow` in `factory_dashboard/static/dashboard.css`, each window `min-width: 180px` and no grow), so each window is as wide as its own words: Claude's rows carry the "use reserve" lever and are wider than Copilot's month, and "5-hour window: 60%" is longer than "week: 5%". The bar fills its window, so the bars come out in three lengths.
- **Colours.** The bar's colour is decided twice, in two templates. The Overview (`factory_dashboard/templates/_partials/allowance.html`) has three: green under the mark, yellow past it, red above 95%. The planning room's lead window (`#lead-window` in `factory_dashboard/templates/planning.html`) has its own copy with only green and yellow, so a window at 97% is red on the Overview and yellow on Planning. The tile's heading is also in the lead's orange, which the Overview's panel heading isn't.

## Expected outcome
The same window draws the same bar on every page: same colour for the same reading, and on the Overview every window's bar has the same length for 100%.

## Done when
- On the Overview at desktop width, Claude's 5-hour, Claude's week and Copilot's month bars are equally long, whatever their words or levers.
- A reading above 95% is red on the Overview and on Planning; past the mark yellow on both; under it green on both.
- The bar's colour rule is written in one place, used by both pages.

## Decisions
- **D1 One bar, one place.** A Jinja macro `allowance_bar(a)` in a new `factory_dashboard/templates/_partials/allowance_bar.html` draws a window's `.meter` (fill colour and mark) from one `WindowAllowance`. The Overview's partial and the planning room's tile both import it; neither keeps its own fill rule. The words around the bar (percent, reset, lever) stay each page's own.
- **D2 Equal columns.** `.allow` becomes a grid of equal columns (`repeat(auto-fit, minmax(220px, 1fr))`), so each window gets the same width and its bar fills it. The phone layout (one row per window, f9-17) stays as it is.
- **D3 After the tickets already on these files.** f9-29 (F9, the week's pace tick) adds to the allowance partial, and f32-01 (F32, the planning tile's reset words) rewrites the tile's rows; F77 waits for both, and the macro carries f9-29's pace tick over unchanged.
- **D4 No mock-up.** This restores the look the bars already meant (one rule, equal bars); nothing new is drawn.

## Tickets
1. `f77-01-allowance-bars-same-width` (developer): the Overview's allowance windows sit in equal columns, so their bars are the same length.
2. `f77-02-one-allowance-bar` (developer): one macro draws a window's bar, used by the Overview and the planning room.
