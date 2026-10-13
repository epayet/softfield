# Milestone F72: I really like the mock up feature, especially to see…

> **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
I really like the mock up feature, especially to see before/after change. This should be the default for frontend features

## Expected outcome
When the owner plants or writes on a card that changes how a page looks, the lead's first reply carries a mock-up with **Today** and **Proposed** of the same page, beside the plan. The owner sees the change before any ticket is queued, and the tickets point at that picture.

## Done when
- The planner's brief (`PLANNER` in `runner/prompts.py`) says when a mock-up is due, what it shows and that the tickets point at it.
- `docs/agents/lead.md` (Planning room) and `docs/agents/owner.md` ("Mock-ups before UI tickets") say the same, so a session in the terminal does it too.
- The next frontend card planned after the merge gets a Today/Proposed mock-up without being asked.

## Decisions
- **D1 When:** a card that changes what a page shows or how it is laid out (a new view, an element added, moved or removed, a new state or colour) gets a mock-up, on the dashboard (`factory_dashboard/templates/`) and in the app (`coucou/templates/`) alike. Not for: wording only, a bug that restores the look a page already meant, or work with nothing on screen. When the lead skips one on a card with screen changes, it says why in a point, and the owner can ask for one.
- **D2 What it shows:** one self-contained HTML file in `docs/milestones/<card>-mockup/`, with a **Today / Proposed** switch at the top: on a phone you flip between two pictures of the same size instead of scrolling from one to the other; on a wide screen they sit side by side. Today is copied from the live template and `factory_dashboard/static/dashboard.css` (or the app's CSS), not redrawn from memory, so it matches what the owner sees. Proposed marks each change (an outline and a short note). Both use real values the lead can read (`var/runs/state.json`, `tasks/`, `docs/milestones/`), as F17's `f17-mockup/top-bar.html` did.
- **D3 Order:** the mock-up and the plan come in the same reply; each UI ticket names the mock-up file in its Context as the picture to build. When the owner's comments change the mock-up, the lead revises the tickets in the same turn. This replaces "iterate the mock-up, then write the tickets" (one round fewer per card).
- **D4 Where the rule lives:** one paragraph in `PLANNER` (the card branch's brief, not `PLANNER_GENERAL`: the general thread drafts nothing), one line in `lead.md`'s Planning room, and `owner.md`'s "Mock-ups before UI tickets" widened from "a new view" to D1, dated 2026-10-09.

## Tickets
| # | id | who | diff | depends | what |
|---|----|-----|------|---------|------|
| 01 | f72-01-mockup-by-default | lead | 2 | – | D1–D4 in the planner's brief, `lead.md` and `owner.md`, with a test on the brief |

## Later
- **The real after, at sign-off:** once a frontend card is built, a screenshot of the live page next to the mock-up's Proposed, on the review page, to see whether the build matches the picture. Needs a headless browser in the runner; goes to `docs/roadmap.md` if the owner agrees.
