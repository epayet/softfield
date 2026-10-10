# F53: a review waiting for Claude doesn't stop the line

The planning thread behind F53's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 12:47

> why is milestone diff review waiting for claude
>
> wasn't copilot supposed to be able to do that? example: [09:09:36] ── f20-data-safety review · round 1/3 ──
> [09:09:36] The whole milestone diff.
> [09:09:36] ▶ [runner] e2e tests
> [09:10:56] ■ [runner] e2e tests passed · 1 min
> [09:10:56] ⏸ [runner] the review waits for Claude (claude: 5-hour window 80% used, over its cap of 75%) · resumes 12:41 (in 3 h 30)

## The lead, 2026-10-08 12:57

> 1. **Copilot was never meant to do the milestone review.** In ADR 16 item 9, Copilot stands in only for the **checkpoint**: a read-only look at the last two merges, which Claude checks again later (f8-08). The review is set to `review = ["claude-opus"]` in `workflow/runner.toml`, and no decision ever gave it a stand-in. So the runner did what it was configured to do. *Action:* nothing.
>
> 2. **The real problem: the whole line stopped for 3 h 30.** All other jobs that wait for Claude (checkpoints, escalations, planner jobs) put their queue row aside until the reset, and the line goes on with other work (ADR 16 item 4). The review is the only one that still sleeps instead (`wait_for_room` in `runner/milestone.py`). On 8 October no commit landed between 09:09 and 12:47, while about 40 developer tickets were ready (f22-01, f32-01, f50-01…) and the local model could have taken them. The 1-minute e2e run was also wasted, because it runs again when the review starts. *Action:* ticket `f53-01-park-the-review` (a lead ticket, because `runner/` is protected). It checks Claude's room before the e2e run. If Claude has no room, the review waits in the queue until the reset and developer tickets run meanwhile. After the reset it goes first again, starting from the round it was at.
>
> 3. **I don't recommend making Copilot the review's stand-in.** The review is the last check before your sign-off: Opus reads the whole milestone diff, runs the checks and writes `docs/reviews/<key>.md` with its sign-off sheet, which F50 now uses to mark a card ripe. Copilot can only read, so it can't write that report. It found 2 of 5 problems on F2's checkpoint test, and a whole-milestone diff would use a lot of its 200 credits a month. Claude would still have to do the full review afterwards, so it saves nothing. Once point 2 is fixed, the wait only delays the review itself, and you sign off later anyway. *Action:* none. If you still want it, it needs a new ADR, because it changes who does a role.
>
> 4. **ADR 22 still holds.** ADR 22 settled that "a due review keeps its place". It still goes first whenever Claude can take it. The only change is that developers now use the hours when Claude can't. I've flagged this anyway, since it changes how that settled point works in practice. *Action:* nothing.
>
> 5. **No repeat found.** F32 is about the reset time on the gauge, F50 about when a card counts as ripe, and F62 about the review's label on the Overview. None of them is about the review stopping the line. *Action:* nothing.
>
> 6. **No pause needed.** The ticket waits in `tasks/later/` until you approve the plan. The review that started all this has already run (round 1 at 12:47). *Action:* approve F53's plan from the dashboard.
>
> 1. **Copilot was never meant to do the milestone review**: Copilot stands in only for the checkpoint (ADR 16 item 9): a read-only look at two merges, which Claude checks again later. The milestone review is set to Claude Opus alone, and no decision gave it a stand-in.
>    Action: Nothing.
> 2. **The real problem: the whole line stopped for 3 h 30**: Checkpoints, escalations and planner jobs wait in the queue and let the line go on. The review is the only job that still sleeps instead. On 8 October nothing ran from 09:09 to 12:47 while about 40 developer tickets were ready, and the e2e run was wasted too.
>    Action: Ticket f53-01-park-the-review (lead): the review waits in the queue until the reset, developer tickets run meanwhile, and it goes first again afterwards.
> 3. **I don't recommend making Copilot the review's stand-in**: The review writes the report and sign-off sheet that you and F50 rely on. Copilot can only read, found 2 of 5 problems on its checkpoint test and has 200 credits a month. Claude would still have to review everything afterwards, so it saves nothing once point 2 is fixed.
>    Action: None. If you still want it, it needs a new ADR.
> 4. **ADR 22 still holds**: The review still goes first whenever Claude can take it. Only the hours when Claude can't go to the developers.
>    Action: Nothing.
> 5. **No repeat found**: F32 (reset time on the gauge), F50 (when a card counts as ripe) and F62 (the review's label on the Overview) are related but different.
>    Action: Nothing.
> 6. **No pause needed**: The ticket waits in tasks/later/ until you approve. The f20 review has already run.
>    Action: Approve F53's plan from the dashboard.
>
> Proposals:
> - F53: a review waiting for Claude doesn't stop the line (plan)

## The owner, 2026-10-09 20:34

> let me see if i understood correctly. so right now, if a whole milestone needs a review but claude can't, it blocks the whole line? and the suggestion is to NOT use copilot to step in, but rather just let other developer work go on? what is the risk of doing that? too many developer work going in a row unsupervised? run me through clearly what happens now and the suggested approach. i'm getting lost with the terminology (checkpoint, review, etc.) and who can do what. what does copilot do then? i understand it's read onlny

## The lead, 2026-10-09 20:39

> You understood it correctly. Below I explain who checks the code at each stage, what happens now, what changes, and the real risk. I also added a "Who looks at the code" section to the F53 doc. The ticket now also makes sure a waiting review only re-reads its own milestone's fixes.
>
> 1. **Yes, you understood it**: Today, when a milestone's review is due and Claude is past its 75%, the whole runner sleeps until Claude's window resets. Nothing else runs, not even the local developer. On 8 October that was 3 h 30 with about 40 tickets ready. My suggestion is not to bring in Copilot but to let the review wait in the queue while developer tickets run. As soon as Claude has room, the review goes first.
>    Action: Ticket f53-01-park-the-review, already drafted.
> 2. **Four layers check the code**: 1) Gates, on every ticket, with no AI: tests, lint and type checks; a ticket that fails them doesn't merge. 2) Checkpoint, after every 2 developer merges: Claude Sonnet reads those two merges and files fix tickets. It is a small, frequent look. 3) Review, once per milestone when all its tickets are merged: Claude Opus reads the whole milestone's changes, runs the end-to-end tests, writes the review report with your sign-off sheet and files fixes, for up to 3 rounds. 4) Your sign-off, after the review.
>    Action: Nothing. This is now written in F53's doc under 'Who looks at the code'.
> 3. **What Copilot does**: Copilot does only the checkpoint (layer 2), and only when Claude has no room. It can read the code but not change files, so it gives its findings as text and the runner turns each one into a fix ticket. When Claude has room again, it re-reads the same merges, because Copilot misses things (on the F2 test it found 2 of 5 problems, with no false alarms). It works on 200 credits a month. It never does the milestone review, because the review has to write the report and the sign-off sheet, which Copilot can't do.
>    Action: Nothing.
> 4. **What happens now, step by step**: A milestone's last ticket merges, so its review is due. The runner picks the review, runs the end-to-end tests (1 min), then checks Claude: 80% used, over the 75% cap. It sleeps until the reset at 12:41. Meanwhile no developer ticket, checkpoint or anything else runs; only your planning-room messages get answered. At 12:41 Claude reviews, and the line restarts afterwards.
>    Action: Nothing.
> 5. **What happens with the fix**: The review is due and the runner checks Claude first (before the e2e run): 80%, no room. The review goes back in the queue marked 'waits for Claude until 12:41'. The local developer takes the next ready ticket, and the next, each passing the gates. Every 2 merges a checkpoint is due: Claude has no room, so Copilot does it and files fix tickets, and Claude re-checks later. At 12:41 the review is picked before any ticket, as now. Checkpoints and escalations already work this way; the review is the last job that still sleeps.
>    Action: Ticket f53-01-park-the-review.
> 6. **Risk 1: developer work while Claude is away**: That work isn't unsupervised: the gates check every ticket and Copilot does the checkpoints. The real gap is when Copilot's month is used up too. Then checkpoints just wait and merges pile up with only the gates checking them, until Claude does one bigger checkpoint over all of them. I think that's acceptable: the local model takes small tickets, nothing is lost, and Claude still reads every merge. It's also what already happens today on any day Claude is busy with something other than a review. I recommend not adding a limit now.
>    Action: Nothing now. If a pile of unchecked merges ever causes a bad merge, I'll propose a cap ('stop developers after N unchecked merges') as an ADR item.
> 7. **Risk 2: the review reading other milestones' work**: While the review waits, other milestones' tickets merge on main. The first round already reads everything since the milestone started, so it gets a little bigger. The bigger problem is a review waiting between rounds: its next round would read the other milestones' merges as if they were its fixes. That wastes Claude's tokens and can lead to wrong findings.
>    Action: Added to the ticket: the next round names only its own milestone's fix merges.
> 8. **Why not Copilot for the review anyway**: Claude would still have to do the full review afterwards, because the report and sign-off sheet need it, so Copilot would add a step without saving any Claude time. A whole milestone's changes would also use a large share of Copilot's 200 monthly credits, which the checkpoints need. With the fix, the only cost of waiting is that the review lands a few hours later, and you sign off later anyway.
>    Action: Nothing. If you still want it, it needs a new ADR.
>
> Proposals:
> - F53: a review waiting for Claude doesn't stop the line (plan)

## The owner, 2026-10-10 09:14

> On point 7: How about if that happens, we do a big review at once of all the milestones that need to be reviewed. A batch milestone review if when Claude has capacity again and multiple milestones need to be reviewed. What would be tradeoffs and benefits of this approach

## The lead, 2026-10-10 09:15

> I weighed the combined review and recommend against it. The plan now records that as decision D3; the ticket is unchanged.
>
> 1. **What a combined review would bring**: Three things. Claude loads the project once instead of once per milestone, which saves some of its window. The end-to-end tests run once instead of once per review (about 1 minute each). And Claude sees the milestones together, so it could spot one milestone undoing another's work. That last one is real: after F4, a plan change in F3 silently removed something F4 had built and no check saw it.
>    Action: Nothing.
> 2. **What it would cost**: 1) Everything after the review is per milestone: the report, your sign-off sheet, the score, the fix tickets, the up-to-3 rounds and the ratings. A combined review would have to be split back into those, which means reworking the review loop, protected code, for several lead tickets. 2) A bigger read is a worse read. F6's review alone hit the 30-minute limit twice, and several milestones at once is where Opus starts missing things. 3) One failure holds everything: if the combined review times out or one milestone needs 3 rounds, every sign-off waits with it. 4) It is one large bite of Claude's 5-hour window instead of several small ones, so it is more likely to hit the 75% cap half-way and wait again.
>    Action: Nothing.
> 3. **It wouldn't fix the problem in point 7**: The unrelated merges a waiting review would read mostly belong to milestones that are still being built, not to ones that are also due for review. A combined review would only cover the finished ones, so the others would still be mixed in. The ticket's rule (the next round names only its own milestone's fix merges) solves it directly and is a few lines.
>    Action: Nothing: already in f53-01-park-the-review.
> 4. **My recommendation: one review per milestone, back to back**: When Claude comes back and several milestones are due, the queue already runs their reviews one after the other, oldest milestone first, before any ticket. You get the 'all at once when Claude is back' effect, each with its own report and sign-off, and one slow review doesn't hold the others' results. Each review's first round reads main as it stands at that moment, so it already sees the other milestones' merged work around its own. I'd come back to a combined review only if the data shows reviews piling up and using too much of Claude's window.
>    Action: Recorded as D3 in F53's doc. No new ticket. Say so if you'd rather try the combined review and I'll draft it as an ADR.
>
> Proposals:
> - F53: a review waiting for Claude doesn't stop the line (plan)
