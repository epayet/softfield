# Milestone F193: The project picker follows the owner's project order

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-02.

## Notes
The project picker at the top should be ordered by project order

## Plan (lead, 2026-11-02)
The picker lists the projects by name: `render` in `factory_dashboard/app.py` has its own query, sorted by name, while the Projects page and the runner read `projects_in_order` in `runner/metrics.py`. One list for all of them.

No mock-up: the control stays as it is, only the order of the names in it changes.

## Expected outcome
- The picker shows the projects in the order of the Projects page. Today that is travel-companion, softfield, coucou, where it shows coucou, softfield, travel-companion.

## Done when
- Open any page and open the picker: the names come in the order the Projects page shows. Change that order on the Projects page; after the runner's next pick, reload a page: the picker has the new order.

## Decisions
- **D1 One order.** `render` takes its names from `metrics.projects_in_order`, which already leaves forgotten projects out and breaks a tie by name. It still adds a page's own project at the end when that project isn't listed.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | picker-in-project-order | D | 1 | – | D1 |

Who builds: a developer. It is small, unprotected, and `factory_wide_status` just above shows the way.
