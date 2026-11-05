# Milestone F219: Lead tickets follow Claude's week pace; runner and dry run share one rule

> **State:** ready · **Priority:** 0 · **Area:** factory
> Planted by the owner on 2026-11-04.

## Notes
Lead tickets don't wait on Claude's week pace line, but --dry-run says they do. Decide which rule holds, then make the runner, --dry-run and the pages agree.

Seen on 2026-11-04: Claude's week was 61% used, with a pace line of 32%. `softfield run --dry-run` listed bug-59 and the other lead tickets as "week 61% used, over its pace line of 32%", yet the runner picked bug-59 (job 1781). The lead told me it would wait, because it trusted the dry run.

What the code does (read in live at b39bf5d3):
- Real pick: `_next_task` in runner/loop.py holds a lead ticket only through `_waits_for_the_owner` and `_at_the_reserve`. `allowance.reserve_only` is true only when the job would dip into the reserve, which starts at 70% of the week with `reserve = 0.3`. A fast lane card or the reserve switch gets past it.
- `work_queue` then calls `dispatch.pick(rows, tickets, dispatch.Windows(), now(), ...)` with empty windows, so that final check sees no allowance. This dates from f8-03 (2026-10-06).
- `_lead_route` calls `router.route` with no windows, so routing doesn't pace a lead ticket either.
- Dry run: `dry_run_plan` builds `dispatch.Windows` from the stored readings, and `dispatch._claude_says` asks `allowance.answer`, which applies the pace line.
- ADR 25 says a job may start only under the pace line, so the real pick goes against an accepted ADR for lead tickets.

Please check:
- Whether the Coming, Overview and factory line pages show the same wrong wait. factory_dashboard/coming.py, overview.py and line.py use the dispatch code, but nobody has looked at what they show.
- Whether lead tickets were paced for real before f8-03, or only in the dry run. ADR 25's evidence is a dry run from 2026-10-06, and it may have been misread the same way.
- What else the pace line should still govern. Developer jobs on cloud agents are paced through `router.route`, and that should keep working.

The decision for me, as an ADR item with your recommendation:
1. Stop at 70% (the lead's recommendation): keep what the runner does, amend ADR 25, and make the dry run and pages say so. Lead work runs while there's allowance and the reserve still protects planning. The cost is that a busy start can leave lead tickets stopped for days.
2. Follow the pace line: make the real pick obey ADR 25. The week spreads out, but at 61% used on 2026-11-04, lead tickets would have waited until about 7 Nov at 18:00 with allowance left.

Whichever I choose:
- A dry run and the runner must agree, with one shared function deciding whether a lead ticket may start. Add a test that gives both the same state and checks they give the same answer, including a week between the pace line and the reserve (61% against 32%).
- runner/ is protected, so the runner change is the lead's ticket.
- If a page changes what it shows, it needs the usual mock-up.

## Plan
- **The owner's decision (2026-11-04):** "I want the pacing and the reserve, towards the end it can use the reserve if available. Critical tickets will be added to the fast lane. Planning is the exception, it can still use the reserve."
- **Expected outcome:** a lead ticket starts only under Claude's week pace line, and in the week's last 10% it may use the reserve. The runner, the dry run and the Overview all say so. Developers, planning and the fast lane go on while it waits.
- **Done when:** a test gives the runner and the dry run the same state and they choose the same next ticket, 65% against a pace line of 33% included; the Overview shows the line, the wait and until when.
- **How to test it:** over the line, the runner takes no new lead ticket off the fast lane, and `softfield run --dry-run` names the developer ticket it takes. Pull the lever, or put the card in the fast lane, and the lead ticket goes.

## Decisions
ADR 44 holds the rule.

- **D1 One function:** `allowance.lead_hold(agent, windows, cost, now, *, reserves=())` returns the reason a lead ticket may not start, or None. A window in `reserves` is a cap on its whole capacity. Otherwise the week is its pace line, and in its last 10% a cap of 100% (the owner, 2026-11-04: "it'd be a shame to lose out on token, I may not do planning"); the 5-hour window is its cap of 75%. A window resting after a refusal holds it. `allowance.answer` doesn't change for anyone else.
- **D2 One path:** the code that chooses the next ticket becomes one function, given what it needs as parameters: the ready tickets, what is done, paused and parked, the windows, the switches and the fast lane cards. `_next_task` calls it from the session; `dry_run_plan` calls it from the files and marks that ticket as next. The dry run's other lines take their wait from `lead_hold`, through `dispatch._ticket_line`.
- **D3 One set of windows:** one helper builds Claude's windows from the readings and the refusals, for both. The dry run reads refusals too.
- **D4 What a hold does:** a lead ticket held by the week is passed over, with no park and no desk item, and the pick asks again each turn. `at_reserve` and its `reserve` parking go, and old entries are cleared at the start of a run. Held by the 5-hour window, it parks only when nothing else can run, as today (`at_five_hour`).
- **D5 Not held:** a fast lane card's tickets, a ticket parked mid-work once its reset has passed, a ticket waiting only for its gates, and every queued job: planner, review, direction, escalation, checkpoint.
- **D6 Keep the pick's empty windows out of the question:** `dispatch.pick` in `work_queue` still receives one ticket, already chosen, so its windows stay empty and its docstring says why: queued jobs park themselves as they start (`claude_hold`). A real window there would pass over a ticket at the 5-hour mark, and it would never park.
- **D7 The Overview** ([mock-up](f219-mockup/lead-stop.html)): f9-29, with its post and stripes, keeps its name, and f61-01, f77-01 and f77-02 go on waiting for it. A plate under the week's meter says lead tickets wait, until about when, and what goes on meanwhile; each held lead row says so. In the last 10% the plate says the whole reserve is open. The mark's words and the legend's line about the mark are corrected: planning and reviews go past it.

## Tickets
| # | Slug | Who | Diff | After | What |
|---|------|-----|------|-------|------|
| 01 | one-lead-rule | L | 6 | | D1 to D6, with the test that the runner and the dry run agree |
| 02 | rewrite-f9-29 | L | 2 | 01 | D7: f9-29 draws the new rule; ADR 25 points at ADR 44 |

## Before and after
- `/`
