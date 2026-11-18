# Milestone F264: The factory should never stay idle. The pacing and reserve…

> **State:** done · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-18. Base: git tag `f264-the-factory-should-never-stay-idle-start`. Report: [`.softfield/reviews/f264-the-factory-should-never-stay-idle.md`](../reviews/f264-the-factory-should-never-stay-idle.md).
> Planted by the owner on 2026-11-18.

## Notes
The factory should never stay idle. The pacing and reserve are to balance local and remote work. If there is lead work available and tokens available and no developer work available, the lead should work. If pacing or past reserve line, developer work should be prioritised. I see the factory is not doing anything ATM

## What happened (2026-11-18)
- The last ticket job ended at 02:04 (review 2361). Since then only probes and planning ran.
- Claude's week: 34% used, today's pace line 26%, mark 70%, resets Mon 23 Nov 16:00. `allowance.lead_hold` holds every lead ticket "until about Thu 19 Nov 01:36".
- Ready: 141 tickets, 101 of them the lead's. Every one of the 40 developer tickets `depends_on` a lead ticket that hasn't run, so `choose_ticket` (`runner/loop.py`) finds no developer ticket and returns None.

## Settled with the owner (2026-11-18)
- The pace line and the 70% mark set the order only: "developers go first, but if no developer and no reviews and no planning, do a lead ticket instead of being idle." Only Claude's real limit stops lead work. The owner accepts the week ending sooner: "I'll shut down my computer if all is done."
- The 5-hour window too: "This breaks the never idle rule, apply it there too. I can still plan, I'll just wait for the answers in the next window." Nothing parks at its 75% mark any more; it only orders.

## Plan
- **Expected outcome:** under the week's pace line and the 5-hour mark, the board's order as today. Over either, queued jobs then developer tickets go first, and when nothing else can start the lead takes the next lead ticket in the board's order. The line stops only at Claude's real limit (100% of a window, or a rest after a refusal) or with nothing ready; nothing parks at the 5-hour mark.
- **Done when:** f264-01, f264-02 and f264-03 are merged.
- **How to test it:** on a day like 2026-11-18 (over the pace, no developer ticket free), `softfield run --dry-run` names a lead ticket as next and the runner starts it; with a developer ticket free, that goes first. The Overview's plate says the lead takes over when nothing else can run.

## Decisions
ADR 50 holds the rule.
- **D1 No new allowance rule:** "held from filling a gap" is `allowance.lead_hold` over `windows.claude` with both `"seven_day"` and `"five_hour"` in the reserves: each window becomes a cap on its whole capacity, so only 100% or a rest holds it; the week's last 10% already answers so. Name it `_held_at_the_limit(windows, at)` in `runner/loop.py`, beside `_passed_over`.
- **D2 The pick:** in `loop.choose_ticket`, while the week's line or the 5-hour mark holds lead tickets (`lead_hold` with `windows.reserves`), developer tickets go first (as today); when none can start and `_held_at_the_limit` is None, the first free lead ticket (review fixes included) is taken, in the board's order. The fast lane and the queued jobs before the pick don't change. In the week's last 10% and with a lever on, nothing holds them already, so the board's order holds (ADR 50 items 5 and 6).
- **D5 No park at the 5-hour mark** (f264-03): `at_five_hour` and its desk item go, and `claude_hold` treats every support job as it treats a planner job (both reserves usable), so a review, direction, escalation or checkpoint waits only for a real limit or a rest. At the start of a run, `FIVE_HOUR_KIND` entries in `state.parked` and their open owner items are cleared (resolved), as ADR 44 did for `at_reserve`. The 5-hour switch stays, meaning "lead tickets keep the board's order past the mark" (D2 reads it through `windows.reserves`).
- **D3 The words:** `_lead_tickets_passed_over` (the idle line) counts a lead ticket as waiting for Claude only when `_held_at_the_limit` holds it, with `allowance.lead_goes_at` on the week as a full window (its reset). F250's `claude_resumes`, built on it, follows. In the dry run (`dispatch._ticket_line`), a lead ticket held by the pace line but not at the limit says "goes when nothing else can (Claude's week over its pace)".
- **D4 The Overview's words** (`factory_dashboard/overview.py`, `_partials/allowance_bar.html`, `_partials/allowance.html`): over the pace, the plate reads "Over pace · developers first; the lead takes over when nothing else can run" and a held lead row "goes when nothing else can"; at 100% or a rest, "lead tickets wait until …" with the reset. The marks' words: the week's "lead tickets go last from here", the 5-hour window's "lead tickets go last from here" (was "kept for you from here"). The switches read "keep board order" (was "use reserve"), and the legend says what they and the marks now do. Words only, on existing elements: no mock-up.

## Tickets
| # | Slug | Who | Diff | After | What |
|---|------|-----|------|-------|------|
| 01 | lead-fills-the-gap | L | 4 | | D1–D3, with tests on the pick, the dry run and the idle line |
| 03 | no-park-at-the-five-hour-mark | L | 3 | 01 | D5 |
| 02 | overview-says-the-lead-fills | D | 2 | 01, 03 | D4 |
