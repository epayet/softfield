# F235: The fast lane goes before planner replies in the multi-project run

The planning thread behind F235's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-09 17:16

> There are items in fast lane, why did they not pick up as soon as Claude limit was available? Instead planner seemed to have gone first

## The lead, 2026-11-09 21:03

> You were right: the planner replies went first, and they shouldn't have. It's a bug in the runner. I've drafted one lead ticket to fix it, and it passes the ticket check.
>
> 1. **What happened today**: Claude's 5-hour limit reset at 16:00. The first thing to run was seven planner replies that had been waiting since 5 and 6 Nov. They ran from 16:00 to 16:19 and cost about $28 (F71's alone was $11.75). Only then did F139's fast-lane ticket (rebuild clashing plan branches) start. Two minutes later it hit Claude's limit and parked until 21:00. At 21:00 it happened again: F234's reply and then this one went ahead of it.
>    Action: Nothing. The fix is point 2.
> 2. **Why: the runner skips the fast lane when it runs every project**: ADR 35 says the fast lane goes before everything, planning included. The part that picks the next job does put it first, and Next in line shows it on top. But softfield run works through all your projects in rounds. Each round first runs every project's queued jobs (planner replies, directions, checkpoints) and only then offers a ticket. So the fast lane never reaches the pick while any planner reply is waiting. This is a bug against an Accepted ADR, not a new rule, so it needs no ADR.
>    Action: Ticket f235-01: each round first runs any project's fast-lane ticket, along with the direction or escalation about it. Then come the queued jobs, then one ticket, as today. It's a lead ticket because runner/ is protected.
> 3. **Your replies will wait behind the lane: pause to get them first**: Once this is fixed, a fast-lane ticket (about 35 minutes each) goes before your planning replies, as ADR 35 chose. When you'd rather have an answer first, pause the factory from the top bar: planning still runs, the lane waits, and resuming carries on. The fix keeps that: while you're paused, the fast lane doesn't go first.
>    Action: Nothing.
> 4. **Those seven replies also used up Claude's window**: About $28 in 19 minutes, mostly from a few long replies that resumed cold sessions. That cost is what F177, Planner replies cost half of Claude, already fixes: its tickets make the planner resume only warm sessions and give each job its own cost. With F235 fixed, the backlog would still run, just after the lane.
>    Action: Nothing new. F177 is already ready, near the top of the board.
> 5. **Put this card at the top of the board**: Until this is fixed, every Claude reset spends the planner backlog first, and your fast-lane cards (F139, The factory folder; F169, Web search for the planner; F85, Sign-off; F9, Line polish) get what's left. Putting F235 itself in the fast lane wouldn't help: that's the bug it fixes. It's one lead ticket.
>    Action: When you approve, drag F235 above F139 on the board.
>
> Proposals:
> - F235: the fast lane goes first in every project round (plan)

## The lead, 2026-11-09 22:28

> Merged F237 here: Why is the first ticket on the board, which is fast lane…

## The owner, 2026-11-09 22:28

> From F237, merged here:
> Why is the first ticket on the board, which is fast lane not being worked on right now

## The lead, 2026-11-09 22:29

> F139's fast-lane ticket isn't running now because of the bug I found earlier on this card, and it would wait hours more. My plan for the fix is unchanged. I've added tonight's numbers to the card.
>
> 1. **Why F139's fast-lane ticket isn't running now**: Same cause as before. From 21:00 three planner replies ran. Then f86-01's direction, its last attempt on Qwen and Opus's escalation ran until 22:22. Then F237's reply and this one ran. The ticket that should go first is F139's, Projects keep Softfield's files in .softfield, not .factory (f139-03), and it has been parked since 16:21. Each round of `softfield run` runs every queued job before it offers any ticket, so the fast lane only gets a turn when that queue is empty.
>    Action: The fix is ticket f235-01, already drafted (the plan below).
> 2. **Next in line is wrong about what runs next**: The Overview lists f139-03 first under 'Fast lane goes before everything'. But behind this reply, eight directions are queued (f228-01, f228-02, f89-03, f198-01, f207-02, f209-01, f225-01, f230-01), plus F89's checkpoint. Without the fix, all nine run before f139-03. Each direction leads to a last attempt on Qwen (f86-01's took 45 minutes) and sometimes an escalation, so the fast lane could wait most of the night. Once f235-01 lands, the page and the runner will agree: Next in line already shows the order ADR 35 asks for.
>    Action: Nothing beyond f235-01.
> 3. **The fix would wait behind those nine jobs too**: f235-01 is an ordinary ticket, so it runs only after the queued jobs, the same way f139-03 does. Putting F235 in the fast lane wouldn't help: that's the bug it fixes. There are two ways forward. (a) Approve it and drag F235 to the top of the board: it lands once the directions are through, probably tomorrow morning. (b) Approve it, and have it landed now in a terminal session (`softfield lead`): about one ticket's work, and then f139-03 goes next. I recommend (b): every Claude reset until then sends the lane to the back.
>    Action: Your choice: (a) wait, or (b) land it now in a terminal session.
> 4. **Directions don't use Claude's window much, but they hold the line**: A direction takes Opus about a minute ($0.77 for f86-01's). It's the last attempt on Qwen that follows it that holds the line for 45 minutes or more, and the fast-lane ticket can't start meanwhile. With the fix, a direction about a fast-lane ticket still goes with that ticket. Other directions go after the fast lane.
>    Action: Nothing.
>
> Proposals:
> - F235: the fast lane goes first in every project round (plan)
