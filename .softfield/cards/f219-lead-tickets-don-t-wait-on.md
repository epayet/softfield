# Milestone F219: Lead tickets don't wait on Claude's week pace line, but…

> **State:** idea · **Priority:** 100 · **Area:** factory
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
