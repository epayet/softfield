# Milestone F69: I want a button to switch from light to night theme

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-09. One developer ticket on the dashboard's existing themes (f5-14).

## Outcome
- A button in the top bar of every dashboard page switches between the light and the night theme, at once, charts included.
- The choice sticks on that device (the phone and the desktop each keep their own); until the owner presses it, the dashboard follows the system as it does today.

## Decisions
- **Words, not a mark:** the button names the theme it switches to ("Night" while light shows, "Light" while night shows), its title "Switch to the night theme" or "… light theme". English only: the dashboard is the factory's (ADR 00 A2).
- **Kept in the browser** (`localStorage`), not on the server: a theme is a device's, nothing to back up.
- **No flash:** a small script in `<head>` sets `data-theme` on `<html>` before the page paints; the stylesheet's light tokens key on `:root[data-theme="light"]` instead of `prefers-color-scheme`.
- **Two states, no "System" choice:** once pressed, the choice stays until pressed again.
- **On a phone it adds no line** to the top bar: what's running stays above the fold.

## Not here
- Themes for Mum's product (coucou): product work is on hold.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | theme-button | D | 3 | – | the top bar's Light/Night button, kept per device, charts redrawn |

## Notes
I want a button to switch from light to night theme
