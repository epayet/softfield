# Milestone F306: On a phone, the arrows to step through points stay put and headlines come first

> **State:** done · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-27. Base: git tag `f306-the-arrows-to-move-between-points-start`. Report: [`.softfield/reviews/f306-the-arrows-to-move-between-points.md`](../reviews/f306-the-arrows-to-move-between-points.md).
> Planted by the owner on 2026-11-26.

## Notes
The arrows to move between points in planning on mobile keep moving depending on the size of the point that's annoying to navigate when glancing through points because I have to find them again each time. The headlines are the most important parts

## Outcome
On a phone, ◀ ▶ stay in the same place while the owner steps through a reply's points or a review's key points, and each point opens on its headline, right under them, so glancing through the headlines is tap, read, tap.

## Today
`factory_dashboard/templates/_partials/deck_nav.html` (dots and ◀ ▶) is included right after the points in `thread.html` and `proposal.html`, and `factory_dashboard/static/deck.js` finds it as the deck's `nextElementSibling`. On a phone one point shows at a time, so the arrows sit under it and move with its length; a long point pushes them under the Send dock. The headline is 15 px body type, the same size as the answer around it.

## Decisions
Mock-up: `.softfield/cards/f306-mockup/arrows-stay-put.html`.

- **D1 The nav goes above the points,** on both pages: in a lead message, after the In short plate (or the Full reply fold) and before the `ol.deck`; on a review, after the "Every key point" line and before `#key-points`. `deck.js` finds it as the deck's `previousElementSibling`. Nothing else moves, and on a wide screen nothing changes (the nav stays hidden there, every point shows).
- **D2 A count in words:** the nav says "Point 2 of 6" above the dots, so the dots aren't the only sign of where you are.
- **D3 The arrows come back into view:** pressing ◀ or ▶ when the nav has been scrolled above the screen (under the sticky top bar) scrolls it back to just under the top bar, so the next headline is where the eye already is. If the nav is in view, nothing scrolls.
- **D4 The headline leads:** on a phone, a point's title (`.point > div > b`, `.key-point > div > b`) is 18 px in `--display`, bold; the answer and the action keep their size.
- **D5 The nav is a plate,** as the mock-up's Proposed draws it: `--plate` with the `--notch` corner and a `--stripe` edge, the arrows on `--bay` with a hazard rule under them. No new token, no status or agent colour.
- **D6 Builds on** the f6-10 deck and its partial; makes nothing removable: it moves the same element and adds no mechanism.

## Tickets
| # | Ticket | Who | Diff. | After | What |
|---|--------|-----|-------|-------|------|
| 01 | arrows-above-the-points | D | 2 | – | D1–D5 |

## Before and after
- `/planning/f305`
- `/planning/f305/proposals/f305-plan`

## Not in this card
- Tapping a dot to jump to a point, or a list of every headline: not asked; the count and fixed arrows should be enough to glance through. A card of its own if not.

## How to test
On a phone, open a thread whose reply has points of very different lengths (F305, Find what writes terabytes to the SSD, has six). Press ▶ five times without scrolling: the arrows never move, and each point starts with its headline right under them. Scroll down a long point and press ▶: the arrows come back to the top of the screen. Do the same on a plan's review. On a computer, both pages look as before.
