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

## The lead, 2026-10-29 08:14

> Approved by the owner on 2026-10-29: approved plan/f177: queued f177-01-own-cost-per-job, f177-02-planner-resumes-only-warm

## The lead, 2026-10-29 08:21

> Merged F189 here: I just talked somewhere about adding new logic to use…

## The owner, 2026-10-29 08:21

> From F189, merged here:
> I just talked somewhere about adding new logic to use --resume Claude if under 5 minutes but not if longer and send the whole thread as new chat instead. Actually, why not --resume all the time? Why the extra logic? Claude might change the cache time over time

## The lead, 2026-10-29 08:22

> Your rule is the right one, though I went the other way: every planner reply now starts a fresh conversation, with no timer. I've rewritten ticket f177-02 and decision D2 on F177's card to match.
>
> 1. **Why not carry on the conversation every time**: Carrying on the conversation is only cheap while Claude still holds it in its cache. After that, a reply first pays full price to load the whole old conversation back, including every file it read. Since 13 Oct, 57 replies came more than an hour after the last one and cost $1.62 each: $92, 42% of what planner replies really cost. That is the money F177 is meant to save, so carrying on every time would keep the very cost we want to cut.
>    Action: Nothing: it's the reason for the change below.
> 2. **You're right that the timer is fragile, so I've dropped it**: The 55-minute rule depended on how long Claude keeps a conversation cached, and that can change, as you say. It also saved very little: only 13 replies since 13 Oct came within the hour, at $0.46 each. Starting fresh instead would cost those few maybe $0.20–0.30 more, about $3 over two weeks. So the simplest rule wins: every planner reply starts a fresh conversation with the thread's history, and there's no clock and no extra logic. A job that a usage limit cuts off still carries on its own conversation as it does now. Ticket f177-02 keeps its file name, which still says 'only warm'; I've rewritten what's inside it.
>    Action: Replan: f177-02 is rewritten as 'always start fresh', and D2 on F177's card says the same.
> 3. **The risk of starting fresh every time**: A fresh reply forgets which files it read last time, but it keeps everything said on the thread: your messages, the lead's replies and every point. The drafts stay on the card's branch, and merged cards' summaries are in the card's notes. At worst, a reply re-reads a few files, which costs cents.
>    Action: Nothing.
> 4. **No need to pause**: F177's tickets are near the end of the board (84 ready ahead of them), so the factory won't reach f177-02 before you approve. Approving swaps in the new version.
>    Action: Nothing.
>
> Proposals:
> - F177: every planner reply starts a fresh conversation (replan)

## The owner, 2026-10-29 18:56

> Isn't it better to keep context from previous investigation rounds though?
> I don't understand why starting fresh is a good idea. Might help with saving but is it best for best answer, it might have to re investigate the same things? Convince me better for one or the other

## The lead, 2026-10-29 20:13

> I still recommend starting fresh, and I've put a better answer behind it than the money. I've also added one line to ticket f177-02 so a fresh reply doesn't have to investigate the same things again. The choice is yours.
>
> 1. **What an old conversation remembers is usually out of date**: When you come back to a thread, it's been 64 hours since the last reply on average (60 such replies since 13 Oct). In the last 64 hours, main took about 300 commits. So the files an old conversation 'remembers' reading are mostly older versions: tickets have merged, functions have moved, the queue has changed. A conversation that carries on trusts what it read before. A fresh one has to read what is there now. Your own rule is to answer from the code, not from memory, and a fresh start follows it.
>    Action: Nothing: it's the main reason for my recommendation.
> 2. **The lead already checks again even with the old context**: Replies that carried on an old conversation still made 18 tool calls each, against 35 for a first reply on a card. Even holding everything it had read, the lead looked again. So keeping the context doesn't stop it re-reading; it just pays a second time to load the old reads back first ($1.61 a reply against $0.46 when you reply within the hour).
>    Action: Nothing.
> 3. **Making a fresh reply just as well-informed**: What's worth keeping between replies is the conclusions, not the raw reads: what was found, what was ruled out and why, and the numbers. These should live in the card's doc, which every reply reads first, the way F177's 'What was found' section does now. I've added one line to the planner's brief for this: keep your findings and what you ruled out in the card's doc, and check the code again before relying on them. This also keeps the knowledge in the repo, where you can read it, instead of inside a hidden conversation that's gone once its card closes.
>    Action: Ticket f177-02 now also adds that line to the planner's brief (cards only, not the general thread).
> 4. **What you give up, honestly**: A fresh reply loses whatever reasoning wasn't written down: a side path the lead tried and dropped without saying so. It re-reads the files it needs, maybe 15–20 tool calls. My estimate is about $1.00–1.10 for a reply on a thread you come back to, not $1.61, so about $13 a week. That's less than the 'under $1' I said at first. The savings are real but modest; the strongest reason is point 1.
>    Action: Nothing.
> 5. **Your choice: start fresh, or always carry on**: I recommend starting fresh, with findings kept in the card's doc (this proposal). The alternative is always carrying on the old conversation: the lead keeps its full memory, at about $13 a week more, with old file reads mixed in with new ones. If you choose that, send this proposal back and I'll set f177-02 aside; f177-01, which corrects the cost figures, stands either way. Approving will tell us within a week: the corrected figures will show the real cost per reply, and the replies you send back will show whether the answers got worse.
>    Action: Approve to start fresh, or send it back to keep carrying on the conversation.
>
> Proposals:
> - F177: every planner reply starts fresh; findings live in the card's doc (replan)
