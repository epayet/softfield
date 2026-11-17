# Milestone F260: Before pictures on the data kept from just before the card's first merge

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-17.

## Notes
The before pictures should be taken on a copy of the database from before the milestone's first merge (or at plan approval), so a milestone that drops a column still gets its before pictures. From F222's review.

## What happens today (read from the code, 2026-11-17)
- Each review round makes one data folder with `prepare` and pictures both trees on it: the after from main, the before from the card's start tag in a worktree (`_round` in `runner/shots.py`, ADR 40 item 2). Only the code differs.
- Softfield's `prepare` copies the live metrics database. The live database is already migrated by main's code, so F222's `_V16` (`ALTER TABLE milestones DROP COLUMN priority`, `runner/metrics.py`) left the old code reading a column that was gone: every before page answered 500.
- A project on sample data has the same trap one step later: `prepare` runs in main's tree, so its data follows main's schema too.

## Outcome
- A card that changes the database still gets its before pictures, from data kept just before its first ticket merged.
- When nothing changed the schema, the before and the after are still drawn on the same data, as today, so their numbers match.
- The page says when a before was drawn on the older data, and from which day.

## Decisions
- **D1: keeping the data.** Just before the squash merge of a card's first ticket (no ticket of the card in `.softfield/tasks/done/` yet, and no kept folder), and only when the card's doc lists pages and the project has `[shots]`, the runner runs the project's `prepare` in a worktree of main as it is before that merge, into `.softfield/var/shots/<key>/before-data/`, with `SOFTFIELD_SHOTS_DATA` pointing there, and writes the day it kept it in `before-data/kept.txt`. One function, `shots.keep_before(repo, key, log)`, called from all three merge paths in `runner/loop.py` (`_merge`, the lead ticket's merge, the escalation's finish). Like `take`, it never raises: a failure is one log line, and the merge goes on.
- **D2: using it.** At the review, the before is tried on today's data first, as now. Only the befores that come back `failed` (not `new`) are taken again, in the same before worktree, on a throwaway copy of the kept data (the app may write to it, and Softfield's `open_db` migrates it forward). Each picture drawn that way records `"data": "<YYYY-MM-DD>"` beside its state in `shots.json`. No kept data, or a failure there too: the picture stays failed, with today's reason.
- **D3: the page.** On the card's page, a plate whose before pictures carry a `data` date captions them "Before · at the card's start, on the data of 5 Nov" (the page's own date format) in place of "Before · at the card's start". Wording in an existing caption: no mock-up.
- **D4: the review.** The line that hands the review its pictures (`runner/milestone.py`, near `shots.read_list`) adds, for befores with a date, that they were drawn on the data of that day, so numbers that differ from the after aren't read as the card's change.
- **D5: clearing it.** The sign-off (`signoff` in `runner/owner.py`) removes `before-data/`; the pictures and `shots.json` stay, as today.
- **D6: ADR 40.** An amendment (drafted on this branch) records D1–D2 against item 2 ("the current `[shots]` commands are used for the before too", one data folder) and the turned-down "taking the before when a card starts".

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | keep-the-before-data | lead | 5 | – | D1, D2, D4, D5: keep the data at the first merge, retry failed befores on it, tell the review, clear it at sign-off |
| 02 | before-caption-says-the-day | developer | 2 | 01 | D3: the caption on the card's page |

01 is the lead's: `runner/` is protected. 02 follows the existing caption in `factory_dashboard/templates/milestone.html`.

## Done when
- A card whose ticket drops a column, with pages listed: at its review the before pictures show the old pages, captioned with the day the data was kept.
- A card that changes no schema: the before is drawn on today's data, as now, and its caption is unchanged.
- The first ticket's merge of a card with pages leaves `.softfield/var/shots/<key>/before-data/`; the sign-off removes it.
- A `prepare` that fails at the merge doesn't stop the merge.
