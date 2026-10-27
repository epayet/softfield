# Milestone F59: A weekly report page: the factory's numbers over time and the lead's read

> **State:** ready · **Priority:** 90 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
(none)

On the thread, 2026-10-23: "I want a report page where I can read and browse previous reports. I'd say weekly, it could be a weekly task by the runner then the tokens are freshly back. I'm thinking something similar to /insights in principle but tailored to this factory. We can talk about what to put on there. Graphs over time would be nice. Jobs done by which agents, time spent, success rate, suggestions for improvement. It should have a global view and a per project view. I want to see how helpful the local agents are. Number of milestones done, where the tokens are being spent, give me more. Can start simple and add more later."

## What we know (2026-10-26)
- Every number the owner asks for is already in the metrics database: `jobs` (role, agent, outcome, started, ended, `cost_usd`), `milestones` (`ended`, `state`), `tickets`, `usage_events`, `runs.project_id`. Savings come from `queries.savings` (`factory_dashboard/queries.py`).
- The week of 19 Oct, the whole factory: 22 milestones done, 122 tickets merged, $305 of Claude (planner replies $150 = 49%, lead tickets $77, reviews $58), the local developer passed 80 of 104 attempts (77%; 36% the week before), 4 timeouts (14 before).
- Claude's seven-day allowance resets on Mondays, 16:00 UTC (`usage_events`, `seven_day`).
- The nearest page today is Agents: totals since the start, one project, no weeks.
- Charts already exist: `data-chart` plus a JSON script, drawn by `factory_dashboard/static/charts.js` (`milestones.html`).
- F132 (The overview shows the whole factory) makes Jobs, Runs and Timeline factory-wide (its D2) and gives `overview.every_project` (D4) and the project plate (D3).
- Related, not repeats: F167 (Is the split between local developers and the lead smart and cheap?) was answered on its thread on 21 Oct; the report answers it again each week. F150 (removed) asked that the factory report review the timeouts: it is a tile. F164 (Plant a review's ideas straight from the review) makes quoted ideas plantable.

## Outcome
A Reports tab where the owner reads one report per week, for the whole factory or one project: the week's numbers and graphs over time, computed from the metrics database whenever the page opens, and the lead's written read with ideas, written once a week by a runner job after Claude's seven-day allowance comes back.

## Done when
- Reports, after Timeline, opens on the newest week; the strip lists every week since 30 Sep, "This week" first
- the week of 19 Oct shows, for the whole factory: 22 milestones done, 122 tickets merged, $305 of Claude, the local developer at 77% (80 of 104), 4 timeouts, each beside the week before
- choosing travel-companion shows its numbers only (8 milestones, $115, 88%)
- the four graphs show every week; "Where Claude's dollars went" puts planner replies first for 19 Oct
- after the first Monday reset once it is built, the runner's first pick writes the week just ended (`.factory/reports/<that Monday>.md`), once, and the page shows its read with its ideas
- a week with no written read says "numbers only" and shows its numbers

## Decisions
- **D1. Numbers are computed, words are written.** The page computes every number from the database each time it opens; no number is stored, and no number comes from Claude's words. So every past week shows from the first day, numbers can't drift from the data, and a new section later shows for old weeks too. Only the read is written, once a week.
- **D2. A week** is Monday 00:00 to the next Monday 00:00 in the machine's local time, named by its Monday ("Week of 19 Oct"). A job counts in the week its `started` falls in; a milestone in the week of its `ended`.
- **D3. The numbers, one function.** `factory_dashboard/reports.py`: `week(conn, projects: list[str], monday: date) -> Week` and `weeks(conn, projects) -> list[date]` (every Monday from the first job's week to this one, newest first). `projects` is `overview.every_project(conn, project)` for the whole factory, or `[name]`. `Week` holds, for that week and the one before it: milestones done; tickets merged (a `passed` job of role developer, last-attempt or lead-ticket, by agent); Claude's dollars by role; hours by agent (`ended - started`); developer attempts and passed, by agent; timeouts; escalations; savings (`queries.savings` summed over the milestones ended that week); plus the series for the graphs over every week (`series(conn, projects) -> list[Week]`, oldest first). The page and the weekly job both read it, so the words and the page agree.
- **D4. The page.** `/reports` and `/reports/<monday>` (`2026-10-19`), in `factory_dashboard/reports.py` with `templates/reports.html`; a tab after Timeline. Factory-wide as F132 D2 says, with its own scope switch "Whole factory · <each project>" (`?scope=travel-companion`). Order: the week strip, The week in numbers (tiles, each with the week before), The lead's read, the four graphs, Who did what. Graphs through `charts.js` with the existing tokens: dollars `--opus`, the local developer `--qwen`; no new colour. Mock-up: `.factory/cards/f59-mockup/reports.html`.
- **D5. The written report is a file in the repo.** `.factory/reports/<monday>.md` in the factory's own project (the registered project whose repo holds `runner/loop.py`, as F164 D2), one per week for every project: `## The whole factory`, then `## <project>` for each project with jobs that week. The page shows the scope's section. The runner commits it, as it does a card. Tool-neutral, in git, readable by another frontier.
- **D6. The weekly job.** Role `report`, on the agent `[roles] report` names, else the first that `[roles] review` names (Opus today). The runner queues it at the first pick after Claude's seven-day window has reset (a `usage_events` reading whose `resets_at` moved past the Monday) when the week before has no file, once; under the reserve, as a planner job is. Its brief, `prompts.REPORT` in `runner/prompts.py`, carries D3's numbers for each scope as text; it may read the database with `softfield look sql`, the week's milestone reviews, and blocked tickets, and writes only its file (`Edit(.factory/reports/*)`). What it writes: what changed and whether it is good, with the numbers it rests on; what went wrong (timeouts, blocks, escalations) and why; then ideas.
- **D7. Ideas are quoted lines,** one sentence each under "Ideas for the factory" or "Ideas for <project>", as F164 D1: so F164's plates can plant them (ticket 04). Until then they show as quotes.
- **D8. No desk item.** A report asks nothing of the owner, so it never shows in Needs you or the notices.
- **D9. Who builds.** 01 developer (Python and its tests, `queries.savings` is the example); 02 lead (a new page with four graphs and the theme; template work cost developers hours in F19 and F28); 03 lead (`runner/` and `runner/prompts.py` are protected; test-first); 04 developer, stretch, after F164's plates.

## Later (start simple, add more)
Each a section that shows for every past week at once (D1):
- time the owner spent: replies, approvals and how long things waited on the desk (`owner_items` created → resolved; F86, idea: tracking time the human spent on a project)
- planning: replies per card, dollars per approved plan
- cost per merged ticket and per changed line, by agent and by project
- ratings by skill (F80, Developer rating could be more tailored to the type of work)
- Claude's allowance: how much of each seven-day window was used, and when it ran out
- why tickets were blocked, grouped
- disk the runs took (F175, Disk space)

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | reports-week-numbers | developer | 4 | – | D2, D3 |
| 02 | reports-page | lead | 6 | 01, f132-02 | D4, D5, D7 |
| 03 | weekly-report-job | lead | 6 | 01 | D5, D6, D7 |
| 04 | report-ideas-plant (stretch) | developer | 3 | 02, f164-03 | D7 |
