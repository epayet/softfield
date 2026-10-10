# F79: when a task times out on the first attempt, is the second…

The planning thread behind F79's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 20:34

> when a task times out on the first attempt, is the second attempt starting from scratch?

## The lead, 2026-10-09 20:42

> I answered from the runner code and wrote the answer on F79's card. I also drafted one small lead ticket, which waits in `tasks/later/` until you approve it.
>
> 1. **No for the code, yes for the conversation**: A second attempt keeps the first one's code, but the developer starts a new conversation. When an attempt times out, the runner commits its edits to the task branch and runs the gates on them. The next attempt works on that same branch and is told: "Your previous attempt ran out of time. Keep what works and finish the smallest remaining piece first", along with the failing gate's output. The branch goes back to main only when the attempt timed out before its first edit, and then there was nothing to keep. What the developer loses is its own earlier conversation and reasoning: each attempt is a new session. Any timeout also gets the lead's direction for the last attempt.
>    Action: Nothing: this is how ADR 12 item 5 and ADR 15 item 7 set it up.
> 2. **Don't resume the timed-out conversation**: You might expect continuing the old conversation to be better. I recommend against it. The local model's context is small, and a session that ran out of time is already nearly full, so resuming it would hit the limit early. A new session that starts by reading the branch is cheaper and works better.
>    Action: Nothing.
> 3. **One gap: the retry isn't told which files it changed**: A developer on OpenCode (the local model) can run only the check commands, not `git diff`. So on a retry it has to re-read files to find out what it did last time. A ticket sent back by the lead already gets a list of the files changed on its branch. A retry after a timeout should get the same list.
>    Action: Ticket f79-01 (lead, because runner/ is protected; small): the retry prompt after a timeout lists the files changed against main.
> 4. **Related to F71 (timeout length), but not the same card**: F71 asks how long the timeout should be; F79 asks what a retry keeps. The answer here makes a timeout cheaper (the work is kept), which matters when you pick F71's value. They are different questions, so I'm not proposing a merge.
>    Action: Nothing; I'll use this answer when replying on F71.
>
> Proposals:
> - F79: the retry after a timeout names the files it changed (plan)

## The owner, 2026-10-10 08:32

> On point 3: Why not also give access to git diff?

## The lead, 2026-10-10 08:33

> Answered from `opencode.json` and the developer prompt; the ticket is unchanged, and the open choice is noted on the card.
>
> 1. **It's possible, and the block is deliberate**: Local developers can't run git because of two things, not an oversight. `opencode.json` denies every shell command except pytest, ruff, mypy, msgfmt and check-all. And the developer's prompt says "never run git", because the runner does all the commits. Allowing `git diff` means changing both. Claude-run developers already have `git diff`, `git log` and `git show`.
>    Action: Nothing: this is the explanation; the choice is point 3.
> 2. **What it would cost**: Three costs.
> 1. The rule gets fuzzier. "Never run git" is short and local models keep to it. "Never run git except diff" invites `git stash`, `git checkout` or `git commit`. Those stay denied, but a denied command returns nothing and wastes time in the attempt.
> 2. It widens what a developer may run, which is a security change (ADR 04 did the same for `msgfmt`, with your approval). `git diff --no-index` can read files outside the repo, which OpenCode otherwise denies. With cloud developers, that content would leave the machine. The rule would have to be narrow: `git diff main*` only.
> 3. The gain is small. To carry on, the developer needs the files as they are now, and it can already read them. A full diff adds what changed, at the price of context the local model is short of.
>    Action: Nothing: these are the reasons behind the recommendation in point 3.
> 3. **Your choice: git diff for local developers**: My recommendation is (a).
> (a) Not yet. Ship f79-01 (the file list in the retry prompt) and look at retries after a timeout once it's in. If they still lose time finding their place, add `git diff` then.
> (b) Add it now, narrowly. I'd draft a short ADR item: allow `git diff main*` in `opencode.json`, and change the prompt to "never run git, except `git diff main` to see your changes". This would be a second lead ticket.
> (c) Add all three read commands (`git diff`, `git log`, `git show`), as Claude developers have. I advise against it: `git log` and `git show` don't help a retry, and they widen the rule further.
>    Action: Pick (a), (b) or (c). With (a), nothing changes and f79-01 stays as drafted. With (b) or (c), I draft the ADR item and the ticket on this branch.
>
> Proposals:
> - F79: the retry after a timeout names the files it changed (plan)
