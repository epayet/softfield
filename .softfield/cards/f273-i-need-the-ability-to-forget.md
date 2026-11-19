# Milestone F273: Forget a project from the Projects page

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-19.

## Notes
I need the ability to forget a project from the web projects page

## What happens today (from the code and the database, 2026-11-19)
- `softfield forget <name>` (`_forget`, `runner/cli.py`) is the only way: it sets `projects.paused` to "forgotten" (`metrics.FORGOTTEN`). The project leaves every list and the runner drops its session; its rows and its folder stay. Five projects are forgotten this way (four test-factory-hello, epayet).
- `softfield init` in a folder of a forgotten project's name asks what to do with the old entry (F136, softfield init asks what to do with a forgotten project of the same name): Continue brings it back.
- Projects can now be started from the Projects page ("Start a project"); waifu-gallery is the first. Nothing on the page takes one away.
- F262, Archive a project (ready, f262-01 to 03), puts an Archive button on each plate and a folded Archived bay under the list; its D6 kept Forget in the terminal only. This card reverses that D6.

## Outcome
From the Projects page the owner forgets an archived project in two presses: it leaves every page and the runner, and nothing is deleted.

## Done when
- f273-01 and f273-02 merged.
- To test: archive coaster-ranker (F262), open the Archived bay, press Forget, read the question, press "Yes, forget it". It turns dashed orange "Forgetting…" at once; at the runner's next pick coaster-ranker is gone from the bay, Needs you and the picker, and `softfield look sql "SELECT paused FROM projects WHERE name='coaster-ranker'"` says forgotten. `softfield init` in its folder offers Continue, which brings it back.

## Decisions
- **D1. Forget from the web is the terminal's forget:** a request kind `forget_project`, on the project's own row, which the runner applies with `set_project_paused(conn, name, FORGOTTEN)`, as `_forget` does. Nothing is deleted (F136's "start fresh" stays the only delete, in the terminal). Results: "forgotten: off every page; `softfield init` in its folder brings it back", "already forgotten".
- **D2. Only an archived project can be forgotten.** Refused otherwise: "archive it first". A live project is archived (F262), then forgotten; this keeps a misclick on a running project's plate from removing it, and the runner holds an archived project's work already, so nothing of it is mid-ticket when forget lands.
- **D3. Not while its app runs.** Refused with "its app is running: stop it first" when its stack is up (`state` in `runner/stacks.py`), so nothing keeps running that no page shows. The dashboard checks before posting; the runner's check is the guard.
- **D4. What goes with it:** a forgotten project leaves the Archived bay, Needs you, the picker and every list (as `softfield forget` today). Its open owner items stay in the database; the question says how many there are ("1 item for you goes with it") so the owner sees them before pressing.
- **D5. The Projects page** (f273-02), as `.softfield/cards/f273-mockup/projects.html` Proposed: in each Archived crate, Forget beside Unarchive, quieter. Pressed, a striped question opens under the crate (no browser pop-up): "Forget <name>?", what leaves, that nothing is deleted and where its folder is, how to bring it back, then "Yes, forget it" and "Keep it". Yes posts the request; Forget turns dashed orange "Forgetting…", disabled, with "On its way…", as Archive does. A crate whose app runs shows its app row (Stop, Logs) and Forget disabled with "Its app is running: stop it first, then Forget."
- **D6. No Forgotten list on the page.** Coming back stays `softfield init`'s Continue (F136). A web "bring back" is a later card if the owner wants it.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | forget-request | L | 2 | f262-01 | D1–D4: the kind, its checks, the runner's words |
| 02 | forget-on-the-projects-page | D | 2 | 01, f262-02 | D5: Forget, the question, on its way, the app row in the bay |

01 is the lead's: `runner/` and `factory_dashboard/requests.py` are protected. 02 follows F262's Archive / Unarchive buttons on the same page.

## Before and after
- `/projects`
