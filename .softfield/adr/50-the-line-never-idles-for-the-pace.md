# ADR 50: Claude's pace and marks set the order, never stop the line

- **Status:** Accepted (by the owner, 2026-11-18)
- **Date:** 2026-11-18
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 44](44-lead-tickets-stop-at-the-reserve.md) items 1, 2, 6 and 8, which hold lead tickets at the week's pace line, at its mark and at the 5-hour window's mark even when nothing else can run; [ADR 16](16-claude-window-and-named-milestones.md) items 1 and 3 and ADR 22 item 4, the owner's 25% of the 5-hour window and its park.
- **Evidence:** [F264](../cards/f264-the-factory-should-never-stay-idle.md). On 2026-11-18 the line stopped after job 2361 (02:04) and ran nothing but planning: Claude's week was 34% used against a pace line of 26%, so all 101 ready lead tickets waited "until about Thu 19 Nov 01:36", and all 40 ready developer tickets wait on a lead ticket that hasn't run. About 23 hours with the local model idle.

## Context
- **What the pace is for:** the owner, 2026-11-18: "The pacing and reserve are to balance local and remote work." "The weekly pacing and 70% marks keep their value, but just in terms of prioritisation, not to pause the whole factory."
- **Lead work is what feeds the developer.** The developer runs on the local model, which costs nothing, but every one of its ready tickets waits for a lead ticket. Holding the lead holds the developer too.
- **Lead tickets are a small part of the week.** Since 9 Nov: planning $284, reviews $71, lead tickets $57 (opus $2.30 a ticket, sonnet $0.36).

## The owner's decisions (2026-11-18)
- "Developers go first, but if no developer and no reviews and no planning, do a lead ticket instead of being idle. I'm aware this may bring the capacity sooner in the week, but I'll shut down my computer if all is done."
- On the 5-hour window: "This breaks the never idle rule, apply it there too. I can still plan, I'll just wait for the answers in the next window."

## Decisions (⚑ = deviates from an earlier decision)
1. **Under the pace line and under the 5-hour mark, nothing changes:** the board's order, lead and developer tickets alike.
2. **⚑ Over the week's pace line, past its mark (70%) or past the 5-hour window's mark (75%), lead tickets go last, not never.** Queued jobs (planning, reviews, directions, escalations, checkpoints) go first as today, then developer tickets; when nothing else can start, the first lead ticket in the board's order runs. Amends ADR 44 items 1, 6 and 8.
3. **⚑ Only Claude's real limit stops Claude's work.** At 100% of a window, or a window resting after a refusal, Claude's jobs wait for the reset as today; a job cut off mid-work parks and resumes (ADR 44 item 7). No window keeps a share back: planning keeps its place first in the line, not its tokens.
4. **⚑ Nothing parks at the 5-hour mark any more:** no lead ticket parks there, no review, direction, escalation or checkpoint waits there, and its desk item ("waits for Claude's 5-hour window, kept for you") goes. Amends ADR 16 items 1 and 3 and ADR 22 item 4.
5. **The week's last 10% puts the board's order back:** tokens left at the reset are lost, so in those hours lead and developer tickets go by the board (what ADR 44 item 2 did, now as an order instead of an opening).
6. **The two levers keep the board's order:** the week's and the 5-hour window's "use reserve" switches now mean "lead tickets keep the board's order past the mark" for their 24 hours, and are named so. The fast lane goes first, as today.
7. **One rule, one path, as ADR 44 item 9:** `loop.choose_ticket` decides for the runner and the dry run; the idle line and the Overview read the same answer.

## Alternatives turned down
- **Stop lead tickets at the week's mark, 70% (the lead's first draft):** turned down by the owner: the mark sets priority, it doesn't pause the factory.
- **Keep the 5-hour window's 25% for the owner (the lead's second draft):** turned down by the owner: it idles the line, and planning can wait for the next window.
- **In a gap, run the lead ticket that frees the most developer tickets first:** a second order beside the board's.
- **Retire the two levers:** fewer controls, but it removes an element from the Overview; they stay with their new meaning until the owner asks.

## Consequences
- **Cost:** at about $1.30 a lead ticket and about $3.10 a point of the week, a day of gap-filling is roughly 25 tickets and 10 points. The week will usually end at its limit, days before the reset.
- **Risk:** when a window reaches 100%, planning replies wait for its reset too: up to 5 hours for the 5-hour window, days for the week. The owner accepts it (2026-11-18).
- **What doesn't change:** the fast lane, planner jobs going first, developer pacing on cloud agents.
