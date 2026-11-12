# Milestone F233: The board's developer's view counts tickets that wait for the lead's direction

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-12. Base: git tag `f233-why-is-the-factory-not-doing-start`. Report: [`.softfield/reviews/f233-why-is-the-factory-not-doing.md`](../reviews/f233-why-is-the-factory-not-doing.md).
> Planted by the owner on 2026-11-06.

## Notes
Why is the factory not doing anything right now but on the board developer view it says there are cards that could be run by devs

## What happened (the lead, 2026-11-09)
- **The line had nothing it could start.** The last developer job ended at 19:05 on 6 Nov; the next job was a planner at 16:00 on 9 Nov, the minute Claude's week reset. Claude's week read 100% from 5 Nov to the reset (the probe at 00:00 on 7 Nov: "You've hit your weekly limit · resets Nov 9, 4pm").
- **Every developer ticket waited for Claude.** Eight had failed twice and waited for the lead's direction (`work_queue` rows of kind `direction`: f86-01, f228-01, f228-02, f89-03, f198-01, f207-02, f209-01, f225-01). Every other ready developer ticket depends on a lead ticket that isn't done (f132-02, f164-03, f9-29, f65-01, …). So the runner was right to wait.
- **The board was wrong.** Its developer's view counts a ready developer ticket with no unfinished lead dependency as "developers: 1 now", and never reads the queued directions. On 9 Nov it said "Developers can work on 7 cards, 10 tickets, about 5 h 48 min" when the true number was 0.
- **Where the week went:** from 2 to 5 Nov Claude jobs cost about $308 API-equivalent, $223 of it planner replies (69 jobs), $44 reviews, $14 lead tickets. ADR 44's Consequences foresaw this; F177, Planner replies: record their real cost, start cold threads fresh, is the fix already planted.

## Decisions
- **D1. A ticket waiting for its direction is the lead's, on the board.** A ready developer ticket with an open `direction` row in `work_queue` counts as "with the lead", as an escalated one does (F206 D3): its card says "developers tried <ticket> · waits for the lead's direction", and it is left out of the "Developers can work on …" line. A developer ticket that depends on it waits for it, named as the lead ticket it waits for.
- **D2. No mock-up:** the look and the tag already exist (F206); only which tickets count, and two words of the tag, change.

## Tickets
- f233-01-direction-is-the-leads (developer)
