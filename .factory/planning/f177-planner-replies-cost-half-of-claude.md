# F177: Planner replies: record their real cost, start cold threads fresh

The planning thread behind F177's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-27 00:53

> Planner replies cost half of Claude's week (19 Oct: $150 of $305, $2.58 a reply): find what makes a reply cost that much and cut it, keeping planning on Opus

## The lead, 2026-10-27 14:01

> I've found why planner replies look so expensive, and drafted two lead tickets on `plan/f177` that fix the cost figure and cut the real cost.
>
> The main finding is that about half of the $150 was never spent: the runner recorded each thread's running total as the cost of every new reply on it. Planning stays on Opus in both tickets.
>
> 1. **About half of the $150 was never spent**: When a planner reply carries on an earlier conversation, Claude reports the cost of the whole conversation so far. The runner stores that as the cost of the new reply alone. So on every thread the recorded costs only go up: 0.92 → 1.10 → 1.18 → 1.26 for replies of 6, 1 and 1 steps. F172's fourth reply was recorded at $14.02; its own cost was $5.22. Only planner replies carry on a conversation this way (other jobs only after a usage limit), so the other figures were right.
>    Action: Ticket f177-01: each job records only its own cost, and the past rows are corrected once.
> 2. **What the week of 19 Oct really cost**: Planner replies cost $71 of $227 (31%), $1.32 a reply. They didn't cost $150 of $305 (49%) at $2.58 a reply. F59, Periodic review of the factory, quotes the old $150, and F153, Sonnet for lead tickets, quoted $194.60. Both come from the same faulty figure. Once f177-01 runs, every page, and F59's review when it runs, will show the corrected numbers.
>    Action: Nothing beyond f177-01.
> 3. **The real waste: replying to a thread you come back to hours later**: Claude keeps a conversation cheap to re-read for about an hour. A reply 25 minutes after the last one read 97k tokens cheaply and paid full price for only 8k. You usually answer hours later. By then, carrying on the conversation means paying full price to load all of it again before doing anything: 239k tokens, $1.92, on F172. Since 13 Oct there were 35 of these late replies at $1.65 each, against 12 replies within the hour at $0.45. Starting a fresh conversation that holds the thread's history as text should bring a late reply down to under $1. That saves about $15 a week, roughly a fifth of the real planner spend.
>    Action: Ticket f177-02: a planner reply carries on the conversation only if the last reply ended under 55 minutes ago. Otherwise it starts fresh with the thread's history, as a new thread already does.
> 4. **The risk of starting fresh**: A fresh conversation forgets the files the lead read last time. The thread's history keeps everything said on it: your messages, the lead's text and every point. The plan's drafts stay on the card's branch for it to read again. At worst, a reply re-reads a few files, which costs cents. Replies within the hour still carry on the old conversation.
>    Action: Nothing.
> 5. **A first reply costs what its work costs**: A first reply on a card averages $1.25 and 36 tool calls. Its cost splits roughly into thirds: re-reading what it has gathered at every step, storing what it reads, and writing tickets and mock-ups. I found no cut there that keeps the same quality on Opus. Each reply also has a fixed cost of about $0.30 for the brief it starts with. So one message holding all your notes for a card is cheaper than several short ones.
>    Action: Nothing. Batching notes is up to you.
> 6. **Small trims I'm leaving alone**: owner.md reaches every lead job twice: CLAUDE.md includes it, and the brief pastes it in again. That costs about $0.05 a reply, about $2 a week. Changing it would reopen F21's decision to paste the brief, made because a mere pointer was skipped, for very little.
>    Action: Nothing.
> 7. **Web search will add to the cost**: F169, Let the planner search and read the web, is ready. Every web page the lead reads stays in the conversation and is paid for again at each later step. With f177-01's correct figures, the cost of those replies will show plainly. If it climbs, the fix is to read fewer, shorter pages.
>    Action: Nothing now.
>
> Proposals:
> - F177: record each job's real cost; late planner replies start fresh (plan)
