# Milestone F266: The over-pace stripe covers the week meter's green fill to its very end

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-18.

## Notes
There's a tiny green dot on the right of the pace slider which annoys me. The pace slider is on top and leaves about a pixel of the green line under

## What happened
When the week is over pace, the meter draws three things in `_partials/allowance_bar.html`: the green fill (from 1px in, `width` = used, rounded), the dashed yellow post (at the pace line) and the hazard stripe over the stretch past the post. The stripe's right edge misses the fill's by 1–4px, for two reasons:
1. the fill starts 1px in from the meter's edge (`.meter > span { inset: 1px auto 1px 1px }`), but the stripe's inline `left` replaces that 1px, so it sits 1px to the left of the fill;
2. the stripe's width is `used - post` rounded on its own, so it can come out a percent short of the rounded fill minus the rounded post (on 2026-11-18: week 36%, pace 26%, stripe 9%, about 3px on the Planning room's bar).

## Decisions
- **D1.** The stripe reuses the fill's and the post's rounded percents: `left: calc(<post>% + 1px)`, `width: <fill>% - <post>%`. Template only; the CSS and the post stay as they are. No mock-up: it restores the look the meter already meant.
