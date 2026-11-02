# F21: the lead's briefs

The planning thread behind F21's plan, oldest first, as it was when the owner approved it.

## The runner, 2026-10-28 11:54

> f21-03-trim-owner blocked: the lead ticket changed nothing.
> Its work is on task/f21-03-trim-owner; its run's logs are in .softfield/var/runs/20261028-090000/f21-03-trim-owner.
> What went wrong, and what is the fix? Propose it as a replan: the ticket reworked, split or set aside.

## The lead, 2026-10-28 11:56

> The trim ticket is blocked for the second time, and this time it isn't a mistake by the job: the ticket can't be done as written. I've drafted a replan that sets it aside.
>
> The only thing pre-flight reports is that the ticket is still in the blocked folder; that goes away when you approve and the runner removes the blocked copy.
>
> 1. **What went wrong: owner.md has grown past the ticket's target**: F21, The lead's briefs, planned this trim when owner.md was 1,380 words. Your rules of 13 and 22 October have since taken it to 1,802. Removing only the stories, as the ticket says, saves about 50 words, and getting under 1,200 would mean cutting a third of the file. That can only be done by rewording or dropping rules, which the ticket forbids. Both runs, on 12 October and today, hit this same wall. The job saw it, undid its edits and left nothing on task/f21-03-trim-owner. It gave up correctly; it wasn't confused.
>    Action: Nothing: this is the diagnosis.
> 2. **Fix: set the ticket aside, and don't requeue it**: Requeuing would only pay for a third run that blocks the same way. The trim saves little: 50 words is about 70 tokens per job, and most of the file is read from cache. I also dropped the word-count test it planned. owner.md grows each time you add a preference, so a ceiling would block the next one. F21 then closes on what it was really for, and that work is done: the planner sees the plan (01) and every job gets its sections (02).
>    Action: Replan f21-03: the ticket moves to .softfield/tasks/later/, and D3 in the card says why.
> 3. **Do you want owner.md reworded?**: A real cut, to about 1,300 words, would mean rewording and merging rules. For example, the four dashboard rules could become one shorter list. You would read the diff before it lands. My recommendation is not to: the saving is small, and your exact words are what the lead follows. The choices are (a) leave it set aside, my recommendation; or (b) bring it back with rewording allowed, at a target you name.
>    Action: Your answer here decides it; with no answer it stays set aside.
> 4. **No need to pause the factory**: This replan only takes a ticket out of the queue and starts nothing. The ticket is blocked, so the line can't pick it up while you decide.
>    Action: Nothing.
>
> Proposals:
> - Set aside f21-03, trim owner.md (replan)

## The lead, 2026-10-29 00:55

> Merged F181 here: The owner asked why f21-03 is blocked and what to do with it. The answer and the replan that sets the ticket aside are already on F21's thread, waiting for the owner's Approve.

## The owner, 2026-10-29 00:55

> From F181, merged here:
> Why is f21-03 blocked? What should I do with it

## The lead, 2026-10-29 00:56

> The set-aside draft is still on plan/f21, unchanged, so this reply answers your question from F181 and lists the replan again for you to approve or reject.
>
> 1. **Why f21-03 is blocked**: The ticket was written to trim owner.md when the file was 1,380 words. Your new rules of 13 and 22 October took it to 1,802. Cutting only the stories, which is all the ticket allows, saves about 50 words. Getting under the target of 1,200 would mean rewording or dropping your rules, and the ticket forbids that. The runs on 12 and 28 October both saw this, put the file back as it was and stopped, so the runner blocked the ticket for changing nothing. Nothing is broken: the ticket asks for something it can't do.
>    Action: Nothing: this is the answer.
> 2. **What to do with it: approve the set-aside**: Press Approve on 'Set aside f21-03, trim owner.md' below. The ticket moves to the set-aside list, and the blocked item leaves your desk. F21, The lead's briefs, can then close on its two finished tickets: the planner sees the plan, and every job gets its sections of lead.md. Running it again would only pay for a third run that blocks the same way. The saving is about 70 tokens per job, mostly read from cache. The factory doesn't need a pause: the replan starts nothing.
>    Action: Approve the replan below.
> 3. **Unless you want owner.md reworded**: Another option is a real cut, to about 1,300 words, made by rewording and merging rules. For example, the four dashboard rules could become one shorter list, and you would read the diff before it lands. I recommend against it: your exact words are what the lead follows, and the saving is small. Your choices: (a) approve the set-aside, my recommendation; or (b) say so here with a target, and I'll rework the ticket to allow rewording.
>    Action: Answer here only if you choose (b).
>
> Proposals:
> - Set aside f21-03, trim owner.md (replan)
