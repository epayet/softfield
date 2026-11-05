# ADR 44: Lead tickets follow the pace line, and stop at the reserve until the week's end

- **Status:** Accepted (by the owner, 2026-11-05)
- **Date:** 2026-11-04
- **Deciders:** project owner (accepts), Claude (drafts)
- **Enforces:** [ADR 15](15-allowance-aware-routing.md) item 1 and [ADR 25](25-pace-with-a-margin.md) for lead tickets, which the runner never applied to them.
- **Amends:** ADR 15 item 1's sweep, for lead tickets; ADR 15 item 5 and [ADR 22](22-one-visible-queue.md) item 4's question about the week's reserve.
- **Evidence:** [F219](../cards/f219-lead-tickets-don-t-wait-on.md). On 2026-11-04 the week was 61% used against a pace line of 32%. `softfield run --dry-run` said lead tickets waited, and the runner started bug-59 (job 1781).

## Context
- **The rule was written and not built.** ADR 15 item 1 paces every fixed window, and ADR 25 kept that with a day's margin. f1-46 (2026-10-01) gave lead tickets only the reserve check, and its test recorded that as correct: "0.5 on a Thursday is past the week's pace line, but not into the reserve".
- **Two pieces of code decide.** The real pick is `_next_task`, which asks only about the reserve. The dry run is `dispatch.plan`, given real windows, which applies the pace line. Since f8-03 the runner has given `dispatch.pick` empty windows, so that check only ever runs in the dry run. They also read different windows, and tell a lead ticket differently (`task.agent` against `router.lead_only`).
- **ADR 25 was written from the dry run.** At 22:50 on 2026-10-06, when it was read, no run was going: run 152 had been interrupted at 22:34, and run 153 started at 23:42. Five lead tickets had run that evening at 13% to 17% used, over that day's 11% line.

## The owner's decision (2026-11-04)
"I want the pacing and the reserve, towards the end it can use the reserve if available." "Critical tickets will be added to the fast lane." "Planning is the exception, it can still use the reserve."

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ A lead ticket starts only under the pace line:** `used ≤ (capacity − reserve) × min(1, elapsed / length + margin)`, as ADR 25 wrote it. This is new in practice: the real pick has never done it.
2. **⚑ In the week's last 10% a lead ticket may use the whole reserve, up to 100% of the week** (amends ADR 15 item 1's sweep, for lead tickets; the owner, 2026-11-04: "it'd be a shame to lose out on token, I may not do planning"). That is the last 17 hours or so, when an unspent reserve is about to be lost. Nothing is kept back for planning in those hours. The sweep doesn't change for other jobs that are paced.
3. **The fast lane and the week's lever get past both.** Critical tickets go in the fast lane (ADR 35 item 4). The lever works as today.
4. **Planner jobs aren't paced** and may use both reserves (ADR 20 item 2).
5. **Reviews, directions, escalations and checkpoints stay as they are:** not paced, and may use the week's reserve (ADR 15 item 4).
6. **⚑ A lead ticket held by the week waits by itself** (amends ADR 15 item 5 and ADR 22 item 4). It is passed over, as a ticket with an unmet dependency is, and goes when the line lets it: no parking, no desk item, no question. Developer tickets go on. The lever stays on the Overview.
7. **Work already begun goes on.** A ticket parked mid-work for a limit resumes at its reset, and a ticket waiting only for its gates runs, whatever the pace.
8. **The 5-hour window doesn't change:** at 75% a lead ticket parks and goes on at the reset, with its desk item and its lever (ADR 16 items 1 and 3).
9. **One decision, one path:** `allowance.lead_hold` holds the rule, and the runner's pick and the dry run share the code that chooses the next ticket, from the same windows. The Overview asks `lead_hold` too. A test gives the runner and the dry run the same state and compares them.
10. **The pace line for developers on cloud agents and for Copilot doesn't change.**

## Alternatives turned down
- **Stop at 70% with no pace (the lead's first draft):** turned down by the owner. The fast lane now covers what can't wait.
- **In the last 10%, up to 90%, keeping the rest for planning:** turned down by the owner. Tokens left at the reset are lost, and they may not plan in those hours.
- **Give the real pick real windows and keep the dry run as it is:** the pick would pass over a ticket at the 5-hour mark, which would then never park or reach the desk. The dry run would still be a second path.

## Consequences
- **Cost:** lead tickets will wait far more than they ever have. 76 of the last 135 lead jobs (56%) ran between the line and the reserve, and 34 ran under the line. 61 of the 105 ready tickets are lead tickets, and developer tickets that depend on them wait too.
- **Risk:** the line rises about 0.42% an hour, and every job counts towards the week, so planner replies and reviews use the same room. In the week of 26 Oct they cost $259 of $322. At that spend, lead tickets run only in what is left. Until [F177, Planner replies: record their real cost, start cold threads fresh](../cards/f177-planner-replies-cost-half-of-claude.md) lands, expect few lead tickets a week outside the fast lane.
- **The week can still run out:** it did so 3.5 to 4.8 days in, in each of the last four weeks, before any last 10% arrived. Pacing lead tickets alone won't change that much, because they cost $18 of that $322.
- **The last hours can end dry:** if lead tickets reach 100% before the reset, planning has to wait for the reset too, and a lead ticket cut off by the limit parks and resumes after it. The lever and the fast lane don't help then, since the limit is real.
- A week's reserve item already on the desk is resolved when this lands.
