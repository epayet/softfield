# Milestone F275: A project started from the Projects page goes first, not last

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-19.

## Notes
a project created by web interface takes first place rather than last place. i usually want it now, so it should be first rather than last

## Plan (lead, 2026-11-19)
Today `register` (`runner/setup.py`) gives every new project the place after the last one, so a project started from the Projects page waits behind Softfield's 143 ready tickets until the owner drags it up and sends (they did exactly that for duck-ascii-test on 2026-11-19). The fix is small: a place in the database, and the plate on the page.

**The picture:** [`f275-mockup/new-project-first.html`](f275-mockup/new-project-first.html), Today / Proposed, on the six projects of 2026-11-19.

## Expected outcome
- A project started from the Projects page is #1 as soon as the runner makes its folder, with no drag or send; its on-its-way plate is drawn at the top of the list from the moment "Start it" is pressed.

## Done when
- On a phone, open `/projects`, start a project: its dashed plate shows at the top of the list. After the runner's next pick it is #1 and the others moved down one place. A project added with `softfield init` in a terminal still comes last.

## Decisions
- **D1 Only a project started from the Projects page goes first.** `register` places a fresh row first when it comes from `start_project` (the "setting up" path); `softfield init` keeps placing it last, since it often brings in an old folder. A forgotten project that comes back keeps its old place, as today.
- **D2 An order sent while the new project waits doesn't push it back.** The page's order is sent without a project the runner hasn't made yet; `set_project_order` puts a left-out project that is "setting up" first, instead of after the listed ones.
- **D3 The plate on the page matches:** the waiting plate (`proj-asked`) is drawn before the first project row, by the template and by the start script.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | new-project-registers-first | L | 2 | – | D1, D2 in `runner/` (protected) |
| 02 | start-plate-on-top | D | 2 | – | D3 on the Projects page; runs beside 01, so the line never waits on the lead alone |

## Before and after
- `/projects`
