# Milestone F123: Projects page: drag projects into order, as on the board

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

The Projects page (`/projects`, ADR 30 item 6) orders projects with a number per project and one
"Send new order" (a `project_order` request, applied at the runner's next pick). The owner
doesn't like arrows and reorders by drag, then one send (owner.md, 2026-10-13). Once F15's
drag-and-send exists on the board (f15-04), use the same drag here and drop the numbers.
Mock-up: .factory/cards/projects-page-mockup/projects.html.
