# Milestone F220: Switching project from an inner page goes back to that tab's own page

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-12. Base: git tag `f220-if-i-m-browsing-a-certain-start`. Report: [`.softfield/reviews/f220-if-i-m-browsing-a-certain.md`](../reviews/f220-if-i-m-browsing-a-certain.md).
> Planted by the owner on 2026-11-04.

## Notes
if i'm browsing a certain discussion or milestone in a project, when i switch project it stays on that planning discutssion or board ticket which is completely different, or even doesn't exist on the other side. it should go back to the overall planning or board instead

## Plan (lead, 2026-11-05)
The picker's form in `factory_dashboard/templates/base.html` has no `action`, so it reloads the address it is on with another `?project=`. An inner page's address means nothing in the other project:
- `/milestones/f193-…` and `/tickets/<id>` answer a bare "Not found", with no top bar to get back with.
- `/planning/f1` opens the other project's F1, a different card under the same number (coucou's is "Retire docs/backlog.md"); `/planning/f220` opens an empty thread on coucou.
- `/jobs/<id>` stays on the same job under the other project's name, and `/projects/<name>` ignores the picker altogether: it looks as if nothing happened.

No mock-up: nothing on the page changes, only where the picker lands.

## Expected outcome
- Switching project from inside a discussion, a card, a ticket, a job or a run lands on that tab's own page for the new project: Planning, Board, Tickets, Jobs, Runs.
- Switching from a page every project has (the Board, Planning, the Milestones list, the Overview…) stays on that page, as today.

## Done when
- f220-01 merged.
- To test: on softfield, open a card from the Board and pick coucou: you land on coucou's Board. Open a discussion from Planning and pick travel-companion: you land on travel-companion's Planning. Open a project's page and pick another project: you land on Projects with that project picked.

## Decisions
- **D1. The picker goes to the tab that is lit.** The form's `action` is the page's `active` address, which every page already sets: a thread and a proposal `/planning`, a card `/board`, a ticket `/tickets`, a job `/jobs`, a run `/runs`, a project's page `/projects`.
- **D2. The Milestones list is the one exception.** It lights Board but every project has it, so it stays on `/milestones`: `milestones_list` passes `"picker_to": "/milestones"`, and the form reads `picker_to`, else `active`.
- **D3. The test follows the picker, not the bar.** F132, The Overview shows the whole factory (f132-08) moves this form into the tab strip, in either order with this card, so the test finds the form by its `select name="project"`. If the move drops the `action`, this test goes red.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | picker-leaves-inner-pages | D | 1 | – | D1–D3 |

Who builds: a developer. It is small, unprotected, and one attribute on a form.
