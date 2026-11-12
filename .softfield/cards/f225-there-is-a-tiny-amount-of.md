# Milestone F225: The night switch slides by itself when a page loads

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-12. Base: git tag `f225-there-is-a-tiny-amount-of-start`. Report: [`.softfield/reviews/f225-there-is-a-tiny-amount-of.md`](../reviews/f225-there-is-a-tiny-amount-of.md).
> Planted by the owner on 2026-11-05.

## Notes
There is a tiny amount of time when the page loads where the night light switch moves from light to night with the orange slider animation which is annoying. Animation not needed on page load, only when changed

## Why it happens
`factory_dashboard/templates/base.html` draws the switch as `aria-checked="false"` (the light side) on every page. The script that reads the theme sets the real value only at `DOMContentLoaded`, after the scripts have loaded, so a page in the night theme can paint first with the knob on the light side. `factory_dashboard/static/dashboard.css` places the knob from `aria-checked` and animates `top`, so it slides. The theme itself is right from the first paint, because `data-theme` is set in `<head>`.

## Decisions
- **D1 The knob follows the theme, not the attribute.** In `dashboard.css`, the knob's place and the lit icon key on `:root[data-theme="light"]`, the value that is already right at first paint. The knob is in its place from the start, so nothing moves on load and no script has to hold the animation back.
- **D2 The animation stays for a real change:** pressing the switch, or the system's theme changing when the owner has made no choice.
- **D3 `aria-checked` and the title stay as they are.** The script still sets them, for screen readers and the tooltip; they just no longer place anything.
- **No mock-up:** the switch looks the same in both themes; only the slide on load goes.

## Tickets
| # | Ticket | Who | What |
|---|---|---|---|
| 01 | f225-01-switch-follows-the-theme | developer | D1 and D2, with their tests |
