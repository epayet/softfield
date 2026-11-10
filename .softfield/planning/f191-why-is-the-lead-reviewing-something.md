# F191: The fast lane goes first under softfield run too, escalations included

The planning thread behind F191's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-29 22:17

> Why is the lead reviewing something not on the fast lane? It reviewed f21 but there were fast lane work to do?

## The lead, 2026-10-29 22:21

> I found the cause and drafted three fix tickets on F191's plan branch. They are not queued yet. Your question is answered in point 1.
>
> 1. **Why F21's review went first**: It's a bug in F172, Mark a card to use Claude's reserve. The fast lane wins only inside one project's pick. `softfield run` runs every project, and each round first runs every project's queued jobs: reviews, planner jobs, checkpoints and directions. No ticket is looked at in that pass, so no fast-lane ticket can beat them. That's how F21's review ran two rounds from 21:06 to 22:17 ($3.16) while F85's and F175's fast-lane tickets were free to run. F172's tests checked the order inside one project's pick, never across a round.
>    Action: Ticket f191-01: each round runs every project's fast lane first, then the queued jobs, then one ticket.
> 2. **A second gap: an escalation drops out of the lane**: When a ticket is escalated, the runner moves it out of the ready tickets, and the fast lane only looks at the ready ones. So its escalation lost its place. Tonight from 20:12 to 20:30, four planner jobs ran before the escalations of F172's and F146's tickets, both in the fast lane. Next in line on the Overview has the same gap.
>    Action: Ticket f191-02 (runner and the dry run) and f191-03 (Next in line).
> 3. **Should your planning replies wait for the lane too?**: ADR 35 says the lane goes before everything, planning included. The bug in point 1 meant your replies on /planning always went first, so you never felt that rule. After the fix, a planning reply will wait behind the lane. F85 and F175 hold six lead tickets, at about 73 minutes each, so a reply could wait most of an evening. I recommend your planning replies stay ahead of the lane: each takes a few minutes, and you are usually waiting at the screen. Choices: (a) replies first, then the lane, which needs a short addition to ADR 35 that I'd draft next; (b) keep ADR 35 as it is, so the lane waits for nothing.
>    Action: The tickets follow ADR 35 as it is. If you pick (a), I draft the ADR item and change f191-01 to match.
> 4. **No mock-up**: Nothing new is drawn. An escalation now shows in the Fast lane bay that F172's mock-up already drew (.factory/cards/f172-mockup/goes-first.html).
>    Action: Nothing.
> 5. **After you approve**: Without help, these three tickets queue behind 99 others. They fix the fast lane itself, so they're worth putting at the top.
>    Action: Drag F191 to the top of the board, or put it in the fast lane from its milestone page.
>
> Proposals:
> - F191: the fast lane goes first under softfield run too, escalations included (plan)

## The owner, 2026-11-02 17:43

> Also, Factory is currently stuck because a review for a fast lane ticket is waiting for Claude tokens to come back. It should continue other developer tickets in the meantime

## The lead, 2026-11-02 22:16

> Your factory stopped because of a bug that isn't specific to the fast lane. I added three tickets to the F191 plan to fix it and put them first. Nothing is queued until you approve.
>
> 1. **Why the factory stopped**: F175, the disk space card, had its review start on 30 Oct at 05:32 with the week at 99%. At 05:54 Claude refused it because the week hit 100%, not resetting until 2 Nov at 16:00. The review then slept where it was. A review runs inside the runner itself, so no job ran in any project for 28 hours, until the run was interrupted on 31 Oct at 10:11. Being in the fast lane played no part: any review would have done this. F53, a review waiting for Claude doesn't stop the line, only checks Claude before a review round starts, not during one.
>    Action: Ticket f191-04: a limit during a round parks the review until the reset, keeping its session, and it carries on from the same round.
> 2. **Agreed: developers keep working**: Developer tickets don't need Claude, so they should keep running. Two other places can stop the factory the same way. One is a review's fix ticket that hits a limit: the review sleeps until the reset. The other is the one-turn repair of a ticket that fails its pre-flight check. Both are in the code, though neither has happened yet.
>    Action: Tickets f191-05 (the fix ticket holds only its own review) and f191-06 (the repair gives up rather than waits).
> 3. **The cost of carrying on**: During a long limit, developer work merges with a lighter check: Copilot's stand-in checkpoint, or none once Copilot's month is used, as F53 already accepted. A developer ticket that fails twice also waits for its direction from Claude, so those jobs pile up and spend the new week's allowance as soon as it resets. I still recommend carrying on, because a stopped factory costs more and the checks still run after the reset.
>    Action: Nothing extra.
> 4. **What still sleeps afterwards**: When no developer ticket is left to run, the runner still sleeps until the reset and ignores your requests meanwhile. bug-02-limit-wait-takes-requests is already in the ready list for this, so I'm not adding a ticket.
>    Action: Nothing new. Drag that bug up the board if you want it sooner.
> 5. **The factory is running again**: The week has reset (7% used) and the runner has been back since 22:10 today. F175's review is still in the queue and will run again, along with the review of F127, shared rules stay shared across projects, and your planning messages.
>    Action: Nothing.
> 6. **This fix goes first**: The stop cost over a day, while the wrong order cost about an hour. So 04, 05 and 06 come before the fast lane order fixes, and 01 now waits for 05. No mock-up, as none of this changes a page: a parked review already shows as waiting for Claude.
>    Action: After you approve, drag F191 to the top of the board or put it in the fast lane, or it waits behind 98 tickets.
> 7. **Still open: should your planning replies wait for the lane?**: You didn't answer this last time, so the tickets still follow ADR 35: once f191-01 lands, a planning reply waits behind fast-lane tickets, possibly for hours. I still recommend (a): your replies go first, then the lane, which needs a short addition to ADR 35. The alternative is (b): keep ADR 35 as it is.
>    Action: Answer (a) and I draft the ADR item and change f191-01. If you say nothing, it stays (b).
>
> Proposals:
> - F191: a Claude limit never stops the factory, and the fast lane really goes first (plan)

## The owner, 2026-11-02 23:06

> I sent back your proposal “F191: a Claude limit never stops the factory, and the fast lane really goes first” (f191-plan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-02 23:35

> The plan still holds against main, and I updated the tickets. But Approve will refuse this plan because of how its branch was moved. I read that from the code rather than pressing it, and point 2 has the fix.
>
> 1. **Checked against main: the plan stands**: None of this work has been done on main. The code these tickets change is as they describe it, and their numbers are still free, so nothing is renumbered or dropped. Today's queue also shows the gap is still there: F175's and F127's reviews parked correctly before starting a round. Only a limit that lands during a round still stops everything.
>    Action: Small updates only: f191-01 and f191-02 no longer name finished tickets, and f191-01 lets its test helper learn the new pass. f191-03 now allows for F192, A fast lane request shows on the board and Overview as soon as it's made, which changes the same lines.
> 2. **Don't press Approve yet: it will be refused**: When F139, Projects keep Softfield's files in .softfield, moved the folder, this branch got its own copy of the move, and it still starts from main of 29 October. So Approve sees 1,341 changed files, runner code included, and refuses them. The runner already tried to catch this branch up with main at the start of this job and couldn't. I can't rebuild a branch from here. Nothing is lost: the drafts are safe on the branch. F82, F51, F140 and F133 have the same problem, and F133's plan has already been refused three times for clashing with main. My fix is for the runner to rebuild a clashing plan branch from main with only its card's drafts. Won't do is not a way out: it deletes the branch and this card too.
>    Action: Plant the text in point 3, then press Refresh against main here once its ticket has merged. The refresh rebuilds this branch and Approve then works.
> 3. **Text for the Plant box (use Plant and ask the lead)**: A plan branch that clashes with main rebuilds itself from main with only its card's drafts: its doc, its mock-ups, its ADRs and its tickets in later/. Today the planner carries on drafting on the clashing branch and Approve refuses it. F139's move left plan/f191, plan/f82, plan/f51, plan/f140 and plan/f133 like this. Put it in the fast lane: F191 waits for it.
>    Action: It has to be a new card: a fix planned here would sit on this same branch and be refused too. The planner starts it on a clean branch. The alternative is a terminal session that rebuilds the five branches by hand. That's quicker today, but the next clash would hit the same wall, so I recommend planting.
> 4. **The factory can still stop until this lands**: A Claude limit during a review can still stop every project until this plan lands. It's most likely near the end of the week, when reviews start at 99%. Your week is at 7% now, so there's time for the steps in point 2.
>    Action: If the week passes about 90% before this lands, turn off nothing but watch for a stop: restarting the runner frees the factory, as it did on 31 October.
> 5. **Your planning replies wait for the lane**: You didn't pick on my earlier question, so ADR 35 stays as it is, as I said it would. Once f191-01 lands, a planning reply waits behind fast-lane tickets, unless you've paused the factory. If you'd rather your replies went first, say so here and I'll draft the ADR item.
>    Action: Written into the card (D1) and into f191-01.
>
> Proposals:
> - F191: a Claude limit never stops the factory, and the fast lane really goes first (plan)

## The owner, 2026-11-05 11:03

> I sent back your proposal “F191: a Claude limit never stops the factory, and the fast lane really goes first” (f191-plan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-05 11:16

> The plan still stands against main, with one ticket narrowed and two widened. Approve will still be refused until the branch fix lands, because the rebuild hasn't happened yet.
>
> 1. **Approve still waits, but you have nothing to plant**: This branch can't be approved yet: it still starts from main of 29 October, and the runner again couldn't catch it up for this job. So my drafts stayed on the old branch. The fix I asked you to plant already exists as f139-03-rebuild-clashing-plan-branches on F139, Projects keep Softfield's files in .softfield. It hasn't run yet and is 7th in line, so skip the Plant text from my last reply.
>    Action: Press Refresh against main once more after f139-03 has merged. The planner job that follows rebuilds this branch and Approve then works.
> 2. **F219 did part of this plan**: F219, Lead tickets follow Claude's week pace, already handles one case: a review whose lead fix is held by the week's pace line now parks instead of paying for another round. A fix ticket parked for a real limit or the 5-hour window still sleeps, though, and so does a parked planner or checkpoint job, which I'd missed before. Your 5-hour window refused Claude five times between 3 and 5 November, so this can happen on any busy day.
>    Action: f191-05 is narrowed to that gap and reuses F219's way out. As in F219, a review's last round records its stop, and the fix runs later in the main queue.
> 3. **A new way to stop everything: an expired login**: bug-59 landed on 4 November. When Claude's login expires, most jobs park, but a review round and a ticket repair wait where they are, checking every five minutes. Every project stops with them until you log in again.
>    Action: f191-04 and f191-06 now cover an expired login as well as a limit.
> 4. **The rest is unchanged**: The lane's order across projects (f191-01) and an escalation keeping its place (f191-02 and f191-03) are all still needed. I only updated their pointers to the code. F85's and F175's tickets, which I used as examples, are done, but the same order fault would hit F171, Each card once on the board, which is in the fast lane now.
>    Action: Tickets updated. They pass their pre-flight check on this branch; Approve checks them again against main.
>
> Proposals:
> - F191: a Claude limit never stops the factory, and the fast lane really goes first (plan)

## The owner, 2026-11-05 13:43

> I sent back your proposal “F191: a Claude limit never stops the factory, and the fast lane really goes first” (f191-plan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-05 15:52

> Nothing relevant changed on main since my last check, so the drafts stay as they are. The hold-up is `f139-03`, the ticket that repairs this branch: it can't start until about 8 November unless you move it.
>
> 1. **Why Refresh changes nothing yet**: This branch can only be repaired by f139-03-rebuild-clashing-plan-branches, on F139, Projects keep Softfield's files in .softfield, and it hasn't run. Each Refresh until then gets the same answer and uses up a planning job. I told you to press it after that ticket merged, but I didn't tell you how long that could take, or how to see that it had happened. I also didn't check since this morning's Refresh whether it could start at all: it can't.
>    Action: Hold off on Refresh. F139's card will show Tickets 2 of 2 done when it's time.
> 2. **Why f139-03 isn't moving**: It's a lead ticket, and F219, Lead tickets follow Claude's week pace, now holds lead tickets once the week is past its pace line. The week is at 93% with four days left. So f139-03 and every other lead ticket off the fast lane wait until the week's last 10% opens, about 8 November at 23:00, or the reset on 9 November at 16:00 if that fills first. F139's page says "next in line", which is misleading: it was written before that rule.
>    Action: See point 3 for the way round it.
> 3. **Your call: put F139 in the fast lane now?**: I recommend yes. Its fast lane lever is on F139's card, under the board, and it holds only this one ticket. It uses some of the 7% left in the week, for a repair that frees five stuck plans. The bigger reason is that reviews, checkpoints and planning jobs still run past the pace line, so the week could reach 100% before it resets. A review caught at that moment stops every project, which is what happened on 30 October. The fix for that is in this plan, and it can't be approved until this branch is repaired. The alternative is to wait for 8 November and spend nothing extra, and if the factory stops before then, restart the runner.
>    Action: Pull the lever on F139's card. Once it shows 2 of 2 done, press Refresh here and then Approve.
> 4. **F191's own tickets will wait for the week too**: All but one of its six tickets are lead tickets. Once approved, they queue behind the pace line like the others. With the week nearly used, I wouldn't put F191 in the fast lane until the new week starts on 9 November, unless the factory stops again before then.
>    Action: After approving, drag F191 to the top of the board. It starts when the lead tickets can.
> 5. **This reply shows the order bug again**: F85's f85-05-fix-slow-page-still-pictured is in the fast lane and free to run, yet this planning job went ahead of it. That's the fault you first asked about on this card, and ticket f191-01 fixes it.
>    Action: Nothing new.
>
> Proposals:
> - F191: a Claude limit never stops the factory, and the fast lane really goes first (plan)

## The owner, 2026-11-05 23:32

> I sent back your proposal “F191: a Claude limit never stops the factory, and the fast lane really goes first” (f191-plan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-05 23:33

> Nothing on main has changed for this plan since my last check, so the drafts stay as they are. Your fast lane lever reached the runner at 23:32, and this planning job then ran ahead of `f139-03` (the ticket that repairs this branch), so the branch is still the old one.
>
> 1. **f139-03 runs straight after this reply**: You pulled F139's fast lane lever at 22:09 and sent this plan back a minute earlier. The runner was busy on a developer ticket that timed out at 23:32, and only then took both requests. It ran this planning job first, so the branch hasn't been repaired yet. f139-03 is in the fast lane and goes next. The week is at 97%, and the fast lane may use what's left of the reserve.
>    Action: Wait for F139's card to show Tickets 2 of 2 done (about half an hour to an hour), then press Refresh against main here once. That planning job rebuilds this branch, and Approve works after it.
> 2. **The order bug, seen once more**: This job ran ahead of a fast-lane ticket that was free to run. That's the fault you first raised on this card, and ticket f191-01 fixes it. Here it cost the hour until f139-03 merges.
>    Action: Nothing new: f191-01 covers it.
>
> Proposals:
> - F191: a Claude limit never stops the factory, and the fast lane really goes first (plan)

## The owner, 2026-11-09 23:05

> I sent back your proposal “F191: a Claude limit never stops the factory, and the fast lane really goes first” (f191-plan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-09 23:09

> The drafts still hold against main. I only added tonight's evidence to the card. This branch is still the old one because `f139-03`, the ticket that repairs it, still hasn't merged, and F191's own bug is the reason.
>
> 1. **Why f139-03 still hasn't merged**: Claude's week ran out on 5 November, so nothing on Claude ran until it reset today at 16:00. Then seven planning replies went first and took Claude's 5-hour window from 14% to 92% in 19 minutes. f139-03, in the fast lane, started at 92% and was refused two minutes in. When the window reset at 21:00, ten more planning jobs, directions and an escalation went ahead of it again, and this reply is one of them. That's the fault this card fixes: under `softfield run`, queued jobs go before fast-lane tickets. I've added this to the card as evidence.
>    Action: Nothing to change in the plan: f191-01 is the fix.
> 2. **When it should run, and how to avoid delaying it**: Eight short jobs are queued: seven directions and a checkpoint, plus one planning reply. They take a minute or two each, and f139-03 should start after them, within about half an hour. The risk is the 5-hour window, at 65% and resetting at 02:00. If those jobs push it to 100%, f139-03 waits until 02:00. Each Refresh, message or plant adds another job ahead of it.
>    Action: Don't press Refresh or send messages on any card until F139, Projects keep Softfield's files in .softfield, shows Tickets 2 of 2 done. Then press Refresh against main here once. That job rebuilds this branch, and Approve then works.
> 3. **What changed on main since last time**: Nothing these tickets touch. Their numbers are still free and their pointers still match the code, so nothing is renumbered or dropped.
>    Action: Nothing.
>
> Proposals:
> - F191: a Claude limit never stops the factory, and the fast lane really goes first (plan)

## The lead, 2026-11-10 17:45

> Merged F238 here: The owner: during a milestone review, the runner should still apply other requests, so planning replies and approvals don't wait. Instead, F9's review (not in the fast lane) ran its fix tickets first. What the lead found (2026-11-10): round 1 ran from 14:24 to 14:51. Then the review's own queue ran f9-35 (14:51 to 15:20) and f9-36 (15:20 to 17:43, two attempts, a direction and a last attempt on the local model). Softfield's requests from 15:28 to 16:42 (a plant, the approvals of F211 and F236, a reorder, two removals) were applied only at 17:30. coaster-ranker's requests (accept ADR 1 and approve M1's plan at 14:31, a plant at 16:37) were still waiting at 17:45, because a review runs inline and every other project waits for it. Still open: the lead proposes to rewrite f191-05 so that, under softfield run, a round's fix tickets run in the main queue, behind every project's queued jobs and requests and ahead of other tickets, with no checkpoint before the next round. A request sent during a long ticket still waits for that ticket to end, as before.

## The owner, 2026-11-10 17:45

> From F238, merged here:
> During a milestone review, the runner applies other jobs requests so that planning response, and approvals don't wait. Currently, a non fast lane milestone review triggered a fix instead of picking up my planning approvals and questions

## The lead, 2026-11-10 17:47

> I've rewritten `f191-05` as a replan. With it, a review hands its fix tickets back to the main queue after each round, so your requests and planning replies no longer wait for them. Please pause the factory before approving it.
>
> 1. **Why your approvals waited during F9's review**: Nothing was limited this time. F9, Line polish, had its review finish round 1 at 14:51 and then run its own fix tickets inside the review, f9-35 and f9-36, until 17:43. Your requests are only taken between jobs in the main queue, so Softfield's waited until 17:30. A review also holds every other project until it ends, so coaster-ranker's acceptance and approval from 14:31 were still waiting at 17:45.
>    Action: Replan of f191-05 (point 2).
> 2. **The change: a review hands its fixes back**: Under `softfield run`, after a round the review stops and goes back to the queue, unless that round was its last. Your requests and planning replies, and every project's queued jobs, then go first. The card's fix tickets come next among tickets, after the fast lane, so the review still gets its fixes promptly. Once they're done, the review comes due again and reads them in its next round. Their merges skip the checkpoint because that round reads them. This replaces the narrower version of f191-05 you approved (which only covered a fix stopped by a Claude limit). Since nothing runs in place after a round, the limit case is covered too.
>    Action: Approve the replan below.
> 3. **What it doesn't fix: the round itself**: A review round still runs while everything else waits: about 30 minutes on Claude (F9's took 27). A request sent during a round still waits for the round to end, and other projects too, just as a request sent during a long ticket waits for that ticket. Making a round itself not block other projects is a bigger change. I'd wait to see whether 30 minutes still bothers you once the fixes are out of the way.
>    Action: Nothing for now. If it still bothers you, plant it and I'll plan it.
> 4. **Fixes go ahead of the board's order**: A card's fix tickets go before other cards' tickets, even ones higher on the board. That's what happens today, since the review runs them straight away. Making them wait their card's turn would leave a review half done for days, with its next round waiting. The fast lane still goes before them.
>    Action: Nothing: it's in the replan.
> 5. **Pause the factory before you approve**: f191-04 is first in line and f191-05 comes straight after it. If the line reaches f191-05 before you approve, it builds the old, narrower version.
>    Action: Press pause in the top bar now. Approving the replan lifts the pause.
>
> Proposals:
> - F191: a review hands its fixes to the main queue, so your requests don't wait (replan)

## The lead, 2026-11-10 17:48

> Merged F240 here: Why is it replying to planning thread lower on project…

## The owner, 2026-11-10 17:48

> From F240, merged here:
> Why is it replying to planning thread lower on project list? There are seeds and approvals pending on coaster ranker but the lead is currently replying to softfield thread

## The lead, 2026-11-10 17:48

> This answers your F240 question on this thread and updates the pending replan of `f191-05` to cover it. The lead is answering Softfield's threads from inside F9's review, so coaster-ranker still waits.
>
> 1. **Why Softfield's threads got answered before coaster-ranker**: F9, Line polish, has had its review open since 14:24. Between rounds the review runs its own project's queue: F9's fixes, then Softfield's other queued jobs, planning replies included. That's why the lead answered F238, F191 and F240, all from inside F9's review. The runner only goes back to your project order between jobs in its main queue, and it won't until the review ends. So coaster-ranker, first in that order, still has three requests waiting: accepting ADR 1 and approving M1's plan (both 14:31), and your plant (16:37).
>    Action: The replan below fixes it (point 2). For today, see point 3.
> 2. **The replan now covers this too**: After each round the review goes back to the main queue. There, your project order decides: coaster-ranker's requests and replies go first, then Softfield's, then F9's fixes. I added a test of exactly this case to f191-05: two projects, the reviewed one second in your order.
>    Action: Approve the replan below. It's the same one as before, with this test added.
> 3. **Today: restart the runner to free coaster-ranker**: F9's review still has a checkpoint and round 2 to run, then probably more fixes, so coaster-ranker could wait hours more. Your pause won't help, because planning jobs still run under a pause. Restarting the runner frees it: F9's review keeps its rounds and starts again from round 2 once it's due. A fresh start goes through your project order, so coaster-ranker's ADR, plan and plant come first. The cost is that F9's checkpoint and round 2 start again later.
>    Action: Restart the runner once this reply shows. If you'd rather not, wait for F9's review to end. Either way, approve the replan.
> 4. **Pause before you approve**: f191-04 is first in line and f191-05 comes straight after it. If the line reaches f191-05 before you approve, it builds the old version.
>    Action: Press pause in the top bar, then approve. Approving lifts the pause.
>
> Proposals:
> - F191: a review hands its fixes to the main queue, so your requests don't wait (replan)
