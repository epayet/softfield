# Milestone F285: I think I said at some point don't do a checkpoint just…

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-21.

## Notes
I think I said at some point don't do a checkpoint just before a review but if I'm out of Claude tokens, copilot could do one checkpoint in case it finds things that the developer can fix before the next review when Claude is back, this should make a stronger case to review. It shouldn't go on an infinite loop of Dev work - Claude out - copilot checkpoint - dev fix - Claude out - copilot checkpoint - new dev fix etc but up to 3 times would be good. 

This is for when let's say Claude is out of tokens on Friday so we can take more time to make the dev tickets a bit better for when Claude is back 

So I think priority order is something like: 
- every 2 dev tickets and there are more dev tickets coming: checkpoint (Claude if available, copilot otherwise unless we think copilot is good for this under copilot pacing rules) 
- last dev ticket before review and there are other dev tickets to do: pick up other dev tickets
- no more dev tickets and a few tickets at ready for review but Claude is out: checkpoint 

What I wrote above might not be completely right, but I think I have a better idea now. Let's introduce a new type of job (better name to be found): optional dev quality check, done by copilot. This job will only happen when all the dev work is done and Claude is not available. It will basically act as a checkoointer to find issues Devs could fix before Claude is back. Less important than already defined dev work, this job can make dev tickets. Not more than 3 times per milestone. Goal is that rather than having factory idle it could improve things
