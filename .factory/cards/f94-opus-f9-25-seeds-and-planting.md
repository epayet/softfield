# Milestone F94: While you were away: who, when and how long, said once

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-10.

## Notes
Opus
f9-25-seeds-and-planting
The field's first two stations show real things: Planting counts the cards being planned with the owner, and tapping the seeds opens the sheet with the set-aside tickets listed, each a link. Opus · finished after 3 developer attempts

i like the new what happened better but:
- if the summary is short, it all shows as one line on desktop
- it says twice who did it, at the beginning and at the end. the beginning is nicer to read, but the endhas slightly more informatio. remove duplicate and bring useful information at the top. it's missing at what time it finished and how long it took overall

## Today (read from the code, 2026-10-10)
The rows are drawn by `factory_dashboard/templates/_partials/away.html` from `away()` in `factory_dashboard/queries.py` (f9-15, f9-34).
- **The name twice:** the row starts with the agent's name (`display_name`) and ends with `label`, which starts with the same name ("Opus · finished after 3 developer attempts").
- **One line when short:** the name, the ticket and the title with its label sit in one wrapping row (`.steps .what`), so a short title stays on the first line and only a long one drops below.
- **No time, no duration:** `away()` already finds each ticket's finish (its last job's end, which orders the list) and reads every job's start, but passes neither to the page.

## Outcome
Each row is always two lines, on a phone and a wide screen ([mock-up](f94-mockup/away-rows.html)):
1. the agent's name, the ticket, how it went ("lead ticket", "1st try", "2 attempts", "finished after 3 developer attempts"), when it finished and how long it took;
2. the ticket's title, alone.

## Decisions
- **D1 The name once, at the start.** `label` no longer carries the name: it is only how it went. A ticket with no `merged_by` still has no name and no label, but shows its finish and duration.
- **D2 Finished:** the end of the ticket's last job (what the list already sorts by), in local time, "finished 10:32"; with the day, "finished 9 Oct 23:05", when that isn't today.
- **D3 Took:** from the start of the ticket's first job to that finish, waits included (a wait for Claude's window counts), written by the `ago` filter: "took 58 min", "took 2.6 h". Working time alone would hide a ticket that sat half a night.
- **D4 The title on its own line,** whatever its length: the facts stay where the eye starts, and rows line up.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | away-row-facts | D | 3 | – | D1–D4 |

Small, unprotected, and follows f9-15's own code: a developer ticket.

## Done when
- On the Overview, no row of While you were away says an agent's name twice.
- Every row shows when its ticket finished and how long it took, on the first line.
- A ticket with a short title shows on two lines on a wide screen, like one with a long title.
