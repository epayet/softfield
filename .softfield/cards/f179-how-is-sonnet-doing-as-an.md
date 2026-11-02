# Milestone F179: Sonnet as the lead on easy tickets: how it does, what it saves, in reports

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-28.

## Notes
How is sonnet doing as an easy lead, how much saving is that doing. Include that in reports too if not already

## What we know (2026-10-29)
ADR 32 (Sonnet does the easier lead tickets) put Sonnet on lead tickets of difficulty 4 or below from 23 Oct; its item 6 asks for a read after about 15. This is that read, from the metrics database (softfield, lead tickets with a difficulty, merged since 6 Oct):
- **Sonnet:** 18 tickets, 17 merged by their first attempt; the one Opus step-up (f90-01) was a flaky test, not Sonnet's code. $11.34, $11.66 with the step-up: $0.65 a ticket. Its six "failed" jobs were all parked by Claude's limit, not attempts.
- **Opus at the same difficulties:** 33 tickets, $57.86, $1.75 a ticket. At Opus's own price per difficulty (2: $0.61, 3: $1.69, 4: $2.27), Sonnet's 18 would have cost about $33.47: **about $21.8 saved, 65%,** in six days.
- **Review findings:** Sonnet's 14 reviewed tickets drew 7 should-fix findings and no blocking one (5.0 per 10); Opus's 28 at the same difficulties 6 (2.1 per 10); Opus's 32 harder ones 13 and 1 blocking (4.1 per 10). The seven were small (a doubled name on the desk, a missed test, a guard too wide), each fixed in its milestone's review.
- **Reports don't show any of it:** the milestone review's Numbers (`runner/report.py`) has a "By agent" row of dollars, nothing per model on lead tickets and no saving; the Agents page's "Who did what" has no lead-ticket column (nor planner), so Sonnet's 25 lead-ticket jobs show nowhere; F59's weekly report (A weekly report page) counts dollars by role, not by model.

## Outcome
The Agents page and every milestone review say how Sonnet does on the easy lead tickets against Opus, and the dollars it saved; the weekly report's read says it each week.

## Done when
- the Agents page shows "Lead tickets, by model" after Efficiency, as in `.softfield/cards/f179-mockup/agents-lead-tickets.html`: softfield's reads about 18 Sonnet tickets, about $21.8 saved
- "Who did what" has a lead-ticket and a planner column (claude-sonnet 25 lead-ticket jobs)
- `softfield report <key>` writes a "Lead tickets by model" table in the review's Numbers, with that milestone's saving and the factory's to date
- the weekly report's brief carries the week's split, so the read can say it

## Decisions
- **D1. Whose ticket.** A lead ticket belongs to the agent of its first lead-ticket job that is an attempt: a job whose note is `parked` or `interrupted` is not one. A later Opus job on it is a step-up; its dollars count on the owner's side ("Sonnet's dollars include its Opus step-ups", ADR 32 item 6). "First time": merged by that first attempt.
- **D2. What Opus would have spent.** For each non-Opus lead ticket merged, Opus's mean dollars per lead ticket of the same difficulty that Opus owned (D1) and merged in the same project, every job with a model recorded; a difficulty Opus never did takes Opus's mean over all its lead tickets. Saved = that sum minus what the ticket's jobs cost. A ticket with no difficulty is left out of the split.
- **D3. One function.** `lead_split(conn, project, key=None, start=None, end=None) -> list[LeadRow]` in `factory_dashboard/queries.py`, beside `savings`: one row per agent and band ("difficulty 4 or below", "difficulty 5 and up", by `[claude] lead_first_up_to`'s 4 written as a constant `EASY_LEAD_UP_TO = 4`), with tickets, merged, first time, step-ups, dollars, would-have (Opus's own rows: none), saved, reviewed (its milestone has a passed `review` job), should-fix and blocking (`findings.severity` on its tickets). `start`/`end` bound the ticket's first job's `started`, for a week. Read-only, as the other queries.
- **D4. The Agents panel.** As the mock-up: the readout says the saving across the project's Sonnet tickets, the two bars to scale, then the table. A project with no non-Opus lead ticket shows no panel. The bars use `--opus` and `--sonnet` (they are those agents' dollars); no new token.
- **D5. "Who did what" shows every role that has a job,** in this order: developer, last-attempt, lead-ticket, direction, escalation, checkpoint, review, planner, then any other in name order (`ROLES` in `factory_dashboard/agents.py` becomes the order, not the filter).
- **D6. The review's Numbers** get "### Lead tickets by model" after "### Savings from delegating": the milestone's rows (D3 with `key`), then an **All milestones** line with the project's saving to date. API-equivalent dollars, as the rest.
- **D7. The weekly report.** `reports.Week` gains `lead: list[LeadRow]` (D3 with the week's bounds), and the `REPORT` brief from f59-03 carries it as text, so the read says how Sonnet did that week. The reports page shows no new tile for now: one can follow once the page is built.
- **D8. The trial's verdict (lead's read, for the owner):** keep Sonnet at difficulty 4 or below; don't widen it to 5 and up. It saves two-thirds on its tickets and merges them first time, but its findings run at twice Opus's on the same tickets, the rate Opus has on the hard ones; widening would put that rate on harder, protected work. Read it again at 40 Sonnet tickets, from the new panel.
- **D9. Who builds.** 01 and 02 developer (`queries.savings` and the Agents page's tables are the examples); 03 lead (`runner/report.py`, `tests/runner/test_report.py` are protected); 04 lead (`runner/prompts.py`), after F59's weekly report job.

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | lead-split | developer | 4 | – | D1, D2, D3 |
| 02 | agents-lead-panel | developer | 4 | 01 | D4, D5 |
| 03 | review-numbers-lead-split | lead | 3 | 01 | D6 |
| 04 | weekly-report-lead-split | lead | 3 | 01, f59-03 | D7 |
