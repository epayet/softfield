# Milestone F262: Archive a project: off the picker, its tickets wait, unarchive any time

> **State:** done · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-27. Base: git tag `f262-i-want-ability-to-archive-a-start`. Report: [`.softfield/reviews/f262-i-want-ability-to-archive-a.md`](../reviews/f262-i-want-ability-to-archive-a.md).
> Planted by the owner on 2026-11-17.

## Notes
I want ability to archive a project so that only active projects are in the project picker. I might unarchive projects at any time and continue planning. 
Archived projects don't get their tickets picked up picked up from the board if there are any

## What happens today (from the code and the database, 2026-11-17)
- The picker in the top bar lists `metrics.projects_in_order` (`page` in `factory_dashboard/app.py`): every project but a forgotten one. A page opened on a project it doesn't list still shows it, last and selected (F193).
- `softfield forget <name>` (`_forget`, `runner/cli.py`) sets `projects.paused` to "forgotten": off every list, rows kept, and nothing on the dashboard brings it back. It is for a folder that is gone, and F136, softfield init asks what to do with a forgotten project of the same name, builds on that meaning.
- F124, Pause one project from the Projects page (ready, f124-01 to 03), makes a project's pause hold its tickets, checkpoints and reviews while its session stays, so its requests and planning still go. Archiving is that hold, plus leaving the lists.
- Projects today: coaster-ranker (0 ready, 12 done), travel-companion, softfield, coucou; five test projects are forgotten.

## Outcome
The owner archives a project from the Projects page: it leaves the project picker and the ordered list for a folded "Archived" bay under it, the runner takes none of its tickets, and everything it holds stays. Unarchive brings it back, running, and its planning goes on where it was.

## Done when
- f262-01 and f262-02 merged (f262-03, the stretch, once F132's floor tickets have landed).
- To test: on the Projects page press Archive on coaster-ranker. It turns dashed orange "Archiving…" at once; at the runner's next pick coaster-ranker is gone from the picker and the list, and sits in "Archived · 1" under it. Open its Board from there: its cards are as they were. Press Unarchive: it comes back at the bottom of the list and in the picker.
- `softfield run --dry-run` says an archived project's tickets are "archived"; a bare `softfield` lists it "(archived)".

## Decisions
- **D1. Archived is a value of `projects.paused`:** "archived", beside "setting up", "forgotten" and F124's time. `metrics.ARCHIVED` names it; `metrics.is_archived(row)` is the one reader. No new column or table.
- **D2. What the runner does with it:** exactly F124 D1's hold: its tickets, checkpoints, escalations and reviews wait; the job running when it takes finishes; the session stays, so its requests (Unarchive among them) are taken and a message on one of its cards still gets the lead's answer. Its activity is `Idle: archived` (the `IDLE` prefix). `--dry-run` gives its tickets the wait "archived". Its ready tickets stay in `.softfield/tasks/ready/` and its board order is untouched.
- **D3. Two request kinds,** `archive_project` and `unarchive_project`, on the project's own row, the database only, as F124 D3's. Archive works on a running or paused project (archived replaces the pause); refused on one being set up ("being set up: `softfield doctor` hands it over"). Results: "archived: off the picker, its tickets wait", "already archived", "unarchived: back in the list, last", "not archived". Unarchive sets `paused` to NULL (running), not back to an earlier pause.
- **D4. Where it leaves, where it stays.** Leaves: the top bar's picker, the Projects page's ordered list and its order form, and the factory-wide status in the top bar (`factory_wide_status`). Stays: its own pages by address (the picker's F193 rule shows it, last and selected), the Projects page's Archived bay, Needs you (anything of it waiting for the owner still shows: the owner's words are never hidden), Runs, Jobs, Timeline and savings history. `projects_in_order` keeps returning it, since the runner needs its session; the dashboard filters with `is_archived`.
- **D5. Order:** an archived project keeps its `priority`, but the order form sends only the listed ones, so it drifts after them (`set_project_order`); unarchived, it comes back last. The owner drags it up.
- **D6. Forget stays as it is:** the terminal's "this folder is gone", which F136 relies on. Archive is the dashboard's reversible shelf. `softfield forget` on an archived project still forgets it.
- **D7. The Projects page** (f262-02), as `.softfield/cards/f262-mockup/projects.html` Proposed: an Archive button at the foot of each listed project's plate, beside its links, quieter than F124's Pause; pressed, dashed orange "Archiving…" with "On its way: the runner takes it at its next pick, after the job it is on", disabled until the request is done (the latest open `archive_project` / `unarchive_project` row, as `order_on_its_way` reads). Under the list, when any project is archived, a `<details>` bay "Archived · N", closed on load; each archived project shows its name, description, "Archived by you", its ready and done counts, Planning and Board links, and Unarchive in hazard yellow, which goes "Unarchiving…" the same way. A project being set up has no Archive button.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | archive-a-project | L | 3 | f124-01 | D1–D3, D6: the value, the kinds, the hold, the runner's words |
| 02 | archive-on-the-projects-page | D | 3 | 01, f124-02 | D4, D5, D7: the picker, the top bar, the Projects page |
| 03 | floor-leaves-archived-out | D | 1 | 02, f132-05 | stretch: F132's Overview lanes and floor draw no archived project |

01 is the lead's: `runner/` and `factory_dashboard/requests.py` are protected. 02 follows F124's Pause button on the same page (f124-02), which lands first.

## Before and after
- `/projects`
- `/planning?project=softfield`
