# Milestone F285: Copilot pre-reviews a finished milestone while Claude is out

> **State:** ready · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-11-21.

## Notes
I think I said at some point don't do a checkpoint just before a review but if I'm out of Claude tokens, copilot could do one checkpoint in case it finds things that the developer can fix before the next review when Claude is back, this should make a stronger case to review. It shouldn't go on an infinite loop of Dev work - Claude out - copilot checkpoint - dev fix - Claude out - copilot checkpoint - new dev fix etc but up to 3 times would be good. 

This is for when let's say Claude is out of tokens on Friday so we can take more time to make the dev tickets a bit better for when Claude is back 

So I think priority order is something like: 
- every 2 dev tickets and there are more dev tickets coming: checkpoint (Claude if available, copilot otherwise unless we think copilot is good for this under copilot pacing rules) 
- last dev ticket before review and there are other dev tickets to do: pick up other dev tickets
- no more dev tickets and a few tickets at ready for review but Claude is out: checkpoint 

What I wrote above might not be completely right, but I think I have a better idea now. Let's introduce a new type of job (better name to be found): optional dev quality check, done by copilot. This job will only happen when all the dev work is done and Claude is not available. It will basically act as a checkoointer to find issues Devs could fix before Claude is back. Less important than already defined dev work, this job can make dev tickets. Not more than 3 times per milestone. Goal is that rather than having factory idle it could improve things

## Plan
- **Expected outcome:** when Claude is at its real limit and no developer ticket or other job can start, Copilot reads a milestone whose review waits for Claude (its card, tickets and changed files) and files developer fix tickets for what it finds. At most three times per milestone, and only after a new merge since its last look. When Claude is back, the Opus review judges what Copilot found.
- **Done when:** f285-01, f285-02 and f285-03 are merged, and ADR 51 is Accepted.
- **How to test it:** on a day Claude is at 100% with a milestone's review parked and no developer ticket free, `softfield run --dry-run` names "Copilot's pre-review of F…" as next; the run's log shows the pre-review, its fix tickets appear in ready for a developer, and the milestone's page lists "Copilot's pre-reviews". A fourth pre-review on that milestone never comes.

## Decisions
ADR 51 holds the rule.
- **D1 The job** (`runner/loop.py`, `pre_review(s) -> bool`): role `pre-review`, by the first agent of `[roles] checkpoint-stand-in` that may run within its pace line: `router.stand_in` takes a keyword `paced: bool = False`; True calls `allowance.answer(..., use_reserve=False)` and its reason says "within its pace". The prompt is `prompts.PRE_REVIEW`, read-only, same JSON answer as `CHECKPOINT_STAND_IN`, given the card doc's path, the done tickets' paths and the files they changed since the git tag `<milestone>-start` (with no tag, the files each done ticket's merge changed, as `_merge_files` does).
- **D2 Which milestone:** the first in `due_reviews` order whose review row is parked or waits for Claude, with fewer than three passed `pre-review` jobs, and a merge of its tickets newer than its last passed pre-review. None → False.
- **D3 When:** in `work_queue`, at the point where the turn would write the idle line and hold: only when `_held_at_the_limit` names a limit and `choose_ticket` returned None and no queued job could start. A pre-review that ran → the turn goes on (its tickets may now be picked). The dry run's next line says "Copilot's pre-review of F…" in the same case (`dispatch`).
- **D4 Its findings:** recorded with `record_findings` under the prefix `<milestone>-P<job id>-` (P for pre-review), so the review judges them. Fix tickets through `fix_tickets`, kept only when the written ticket is `agent: developer` and touches no protected path; any other written ticket is removed again and its findings stay recorded with route `report`. No `recheck` entry.
- **D5 The words:** runner note and commit "pre-review of F… (by copilot-auto, while Claude is out): N findings; fix tickets: …". Dashboard (f285-03): `ROLE_LINES["pre-review"] = "Copilot reads {key} before the lead's review"` in `factory_dashboard/overview.py`, and `_ROLE_LABELS["pre-review"] = "Copilot's pre-reviews"` in `factory_dashboard/milestones.py`. Words on existing rows only: no mock-up.

## Tickets
| # | Slug | Who | Diff | After | What |
|---|------|-----|------|-------|------|
| 01 | pre-review-job | L | 4 | | D1, D4: the job, its prompt, its findings and tickets |
| 02 | pre-review-when-idle | L | 3 | 01 | D2, D3: which milestone, when, the dry run |
| 03 | pre-review-words | D | 1 | 01 | D5's dashboard words |
