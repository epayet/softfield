# Milestone F86: idea: tracking time the human spent on a project

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
idea: tracking time the human spent on a project

## What we know (2026-10-27)
- Every press and message the owner makes on the dashboard is a row in `owner_requests` (`kind`, `subject`, `project_id`, `created`): 859 since 7 Oct, nothing before. Messages on threads, approvals, sign-offs, plants, pauses, reorders, reserves.
- Nothing records reading without pressing, and nothing records the owner's terminal sessions.
- Grouping the actions into sittings (a gap of more than 20 minutes starts a new one) gives, by week: 5 Oct 12.5 h (from Wed 7 Oct), 12 Oct 12.8 h, 19 Oct 11.5 h. The week of 19 Oct: 28 sittings on 6 days, 244 actions (90 messages, 27 approvals, 22 sign-offs, 32 plants); 8.4 h on softfield and 3.1 h on travel-companion; planting took the most (95 min, 32 plants), then steering the line (87 min: pauses, reserves, reorders), then travel-companion's F1 thread (38 min) and softfield's F172 (33 min).
- Card keys repeat across projects (softfield's F1 and travel-companion's F1), and `subject` is sometimes the whole slug (`f158-milestones-don-t-…`).
- How long things waited on the desk is in `owner_items` (`created` → `resolved`): the median item resolved the week of 19 Oct waited 5.5 h (62 items), 8.2 h the week before.
- `created` is stored with its offset, and the offsets vary (`+01:00`, `+00:00`): ordered as text, the gaps come out wrong (a first try gave 5.5 h for 19 Oct instead of 11.5 h). Order and subtract as datetimes.
- F59 (A weekly report page: the factory's numbers over time and the lead's read) is ready and lists this card in its "Later": the owner's time is one more section of its report, beside the factory's numbers.

## Outcome
The weekly report shows how much of the owner's time the factory took, for the whole factory or one project: hours on the dashboard beside the week before, how long things waited for them, which cards took their time, and the owner's hours in the hours graph beside the agents'. The lead's weekly read says where that time went and how to save some.

## Done when
- the week of 19 Oct, whole factory, shows "Your time 11.5 h" with "12.8 h the week before", and "Waited for you 5.5 h" (median, 62 items) with "8.2 h the week before"
- choosing travel-companion shows 3.1 h and its own cards only
- "Where your time went" lists, for 19 Oct, Planting first (1 h 35), then Steering the line (1 h 27), then travel-companion F1 (38 min) and F172 (33 min)
- the hours graph has a bar for the owner each week from 5 Oct; the week of 28 Sep says "not recorded"
- the page says the time is counted from the dashboard only, terminal sessions not included
- the first weekly read written after this is built has a paragraph on the owner's time

## Decisions
- **D1. Counted from presses, not watched.** The owner's time comes from `owner_requests` only: no page beacon, no new table, nothing stored. So every week since 7 Oct shows at once (F59 D1), and the dashboard sends nothing new from the phone. It undercounts reading that ends in no press, and terminal sessions don't show: the page says "on the dashboard".
- **D2. Sittings.** All actions of every project, ordered by `created` as datetimes. An action less than 20 minutes after the one before continues the sitting and counts that gap; any other action starts a sitting and counts 5 minutes (the reading before the first press). Each action's minutes go to its week (F59 D2: the week its `created` falls in, local time), its project and its card. Hours = the sum.
- **D3. Its card.** The leading key of `subject` (`f172`, `f158-milestones-…` → `f158`, `m1` → `m1`), kept with its project (two projects can both have an F1), shown with the card's title; for the whole factory, a card of another project than the factory's own is prefixed with its project. A `plant` → "Planting". Anything else with no key (pause, resume, reorder, project order, a reserve on `five_hour`) → "Steering the line".
- **D4. Waited for you.** The median of `resolved - created`, in hours, over the `owner_items` resolved in the week; None with none resolved.
- **D5. The function.** In `factory_dashboard/reports.py`, after F59's ticket 01: `owner_time(conn, projects, monday) -> OwnerTime` with `hours`, `hours_before`, `sittings`, `days`, `actions` by kind, `by_card` (list of (card key or label, title, minutes), most first), `waited_hours`, `waited_hours_before`, `waited_items`. `Week` gains `owner: OwnerTime`, and `series` carries `owner.hours` for every week (None before the first `owner_requests` row). The page and the weekly job both read it (F59 D3).
- **D6. The page.** On F59's Reports page, built by f59-02: two tiles at the end of The week in numbers ("Your time", "Waited for you"); a panel "Where your time went" after the four graphs (bars, top 6 cards, then "Everything else"; under it sittings, days and actions by kind); and the owner as a third part of each bar in "Hours worked, by agent". New token `--owner` for the owner's part, plain ink (`var(--fg)` in both themes), so it never looks like an agent or a status. Mock-up: `.factory/cards/f86-mockup/your-time.html`.
- **D7. The read.** `prompts.REPORT` (F59 D6) carries `owner_time` as text with the other numbers and asks for one paragraph on where the owner's time went and, when it can, one idea that saves some (as a quoted line, F59 D7).
- **D8. Who builds.** 01 developer (Python and its tests, after f59-01, which it follows); 02 developer (two tiles, one panel and a bar part on a page that exists, following f59-02's own sections); 03 lead (`runner/prompts.py` is protected).

## Later
- reading time: a beacon while a page is open and visible, if the presses turn out to miss too much
- the owner's minutes on each milestone's own page, beside its dollars
- terminal sessions, from their commits or the lead's session logs

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | owner-time-numbers | developer | 4 | f59-01 | D1–D5 |
| 02 | your-time-on-reports | developer | 4 | 01, f59-02 | D6 |
| 03 | report-reads-your-time | lead | 3 | 01, f59-03 | D7 |
