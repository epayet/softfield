# F65: review rounds until you sign off

The planning thread behind F65's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 18:30

> The lead is reviewing stuff but I don't know what it is it doesn't tell me. I believe this is planned, verify that it is and prioritise it

## The lead, 2026-10-08 18:32

> The lead merged F65 into F62: its notes are on F62's card now. The conversation goes on on F62's thread: /planning/f62

## The lead, 2026-10-08 18:32

> F65 asks for the same thing as F62, so I'm proposing to merge it into F62. I checked the code, and nothing beyond F62 plans this fix yet.
>
> 1. **F62 already asks for this**: You planted F62 earlier today: "claude-opus review on overview does not say what it reviews". That's the same complaint as F65. F62 is still only an idea, with no plan and no tickets. Nothing else covers it: F10's crates and F17's status dot change how a job is drawn, not what it says.
>    Action: Merge F65 into F62 (the older card). Your note moves there and the conversation continues on F62's thread.
> 2. **Why you can't see it**: A review job isn't tied to a ticket, so the Now card shows only 'claude-opus · review · job 123', and the top bar says 'Running: review, job 123'. The database already records which milestone each job is for, but neither place shows it. So this is a small display fix, not new tracking.
>    Action: One ticket on F62: wherever a job has no ticket (review, checkpoint, direction, escalation, planner), show its role in words plus its milestone with a link, e.g. 'Reviewing F50: The data safety review…', on the Now card, the top bar and the Planning page's 'Running' line.
> 3. **Making it a priority**: I agree it should jump the line. It's cheap (one template and the top bar's wording) and it fits your rule that what's running comes first. A developer can build it: it's small, unprotected, and follows how a ticket's title is already shown.
>    Action: After the merge, I'll draft F62's plan with this single ticket, marked to run next, for you to approve. I'm not drafting it on plan/f65, because drafts there would block the merge.
> 4. **Should it also say what the review found?**: Knowing the milestone tells you what is being reviewed, but not why the review matters to you. The review's verdict already appears in Overview's verdict panel once it's done. Showing findings live while the review runs would cost more, because the runner would have to stream them, and I don't think it's worth it now.
>    Action: Nothing for now. If you still want the live findings, add it as a note on F62.
>
> Proposals:
> - F65 joins F62: say what the lead is reviewing (merge)

## The owner, 2026-10-09 07:45

> What happens if I comment on a signoff/review thread? I essentially want it to iterate until I'm happy to sign off, it should show me the things it changed to see if I'm happy with the new iterated work, how clear will that be?

## The lead, 2026-10-09 07:50

> Today, commenting on a card that waits for sign-off doesn't show you what changed: once the follow-up work is done, no new review runs, and the card comes back with the old review. I've drafted a plan so each comment starts a round that you can see.
>
> 1. **What happens today when you comment**: Your comment goes to the lead like any other planning message, but the lead isn't told the card is built and waiting for you. It can draft follow-up tickets, and Approve plan queues them. That part works.
>    Action: Ticket f65-02: the lead is told the card waits for your sign-off and sees its 'What changed', so it treats your comment as feedback on built work.
> 2. **The gap: you'd see the old review**: Once the follow-up tickets are done, no new review runs, because the runner remembers the first one as finished. The card comes straight back to your desk with the first build's 'What changed' and nothing about your change. So right now it would not be clear at all.
>    Action: Ticket f65-01: approving follow-up tickets starts a round. The card leaves the desk until the work is done, then a short review of just that round's changes writes a 'This round' section.
> 3. **How it will look**: The card's page opens on 'Round 2: what changed since your comment', with your comment quoted, each change, how to test it, and the round's tickets and changes linked. Earlier rounds fold underneath. Under Sign off a line says 'Not happy yet? Reply below', so you can keep going until you sign off. The mock-up uses F50 as the example.
>    Action: Ticket f65-03, built by a developer, following docs/milestones/f65-mockup/round.html. Comment on the mock-up if anything should look different.
> 4. **One approval tap per round: keep it?**: I recommend keeping it: comment, the lead answers with drafted tickets, you tap Approve plan. The tap is where you check it understood you before an hour of work. Alternatives: (a) your comment counts as approval when the follow-up is small (two or fewer developer tickets), which is faster but breaks your rule that nothing is queued without your approval; (b) the lead fixes small things itself, straight away with no tickets, which is fastest but skips the tests on the line.
>    Action: Keep the tap (as planned). Say (a) or (b) if you'd rather.
> 5. **Follow-ups jump the queue**: Changes you're waiting to sign off shouldn't sit behind the backlog, so a waiting card's follow-up tickets get priority 0.
>    Action: Part of f65-01 (D5).
> 6. **Cost of each round**: Each round adds one review job on Opus, but only over that round's small diff, so it usually stops after one pass. That's a few dollars per round, against seeing exactly what changed before you sign off. Rounds are unlimited, because you decide when it's done.
>    Action: Nothing. The review report records each round's cost as it does today.
> 7. **A workflow change without an ADR**: This changes the review rule from 'one review per card' to 'one review per round'. Normally that's an ADR for you. Because it's small and you approve the plan anyway, I've put it in F65's Decisions (D1–D2) instead.
>    Action: Approve the plan as is. Say so if you want it as an ADR item.
>
> Proposals:
> - F65: review rounds until you sign off (plan)
> - A card's page after a review round (mockup)

## The lead, 2026-10-09 20:34

> Approved by the owner on 2026-10-09: approved plan/f65: queued f65-01-review-rounds, f65-02-feedback-prompt, f65-03-round-on-page

## The lead, 2026-10-29 07:53

> Merged F183 here: Asked: a card whose follow-up plan the owner approved shouldn't wait on the desk for sign-off until that work is done, unless the owner cancels the plan.
> Found: once the runner has taken the approval, ready tickets already keep the card off To sign off (F172, F38, F68, F69 today). Still open: (a) between Approve and the runner's pick, the card stays in To sign off and a Sign off press is refused (F38: approved 00:24, sign-off refused 00:50 on 2026-10-29; F172 and F69 waited 07:36 to 07:50); cancelling the approval, or setting the new tickets aside, should bring the card back. (b) F142's sign-off: done in git on 10-28 (dd2f7e6, tag exists), never recorded in the database, so every press fails on `git tag … already exists` (requests 910, 921; 929 pending) and the card stays Ripe. It needs a fix ticket first in line.

## The owner, 2026-10-29 07:53

> From F183, merged here:
> When I haven't signed off a ticket and approved a plan to do some more work on top of it and the work is not done, it should not be on by desk for.me to sign off, unless I cancel the related plans that change it

## The lead, 2026-10-29 08:03

> Merged F182 here: When I don't sign off a card and comment on it instead, I…

## The lead, 2026-10-29 08:03

> Your note is right. Once the runner takes your Approve, the card already leaves To sign off. The gap is the time before that pick, and there's no way yet to cancel a round from the dashboard. This replan closes both, with a mock-up, and merges F182 here.
>
> 1. **Agreed: approved follow-up work takes the card off To sign off at once**: Once the runner has taken your Approve, the card's new tickets are ready, and that already keeps it off To sign off. That's why F172, F38, F68 and F69 aren't there now. Two gaps are left. First, between your press and the runner's next pick, the card stays in To sign off, and Sign off is refused at the pick. F38 shows this: you approved at 00:24, pressed Sign off at 00:50, and at the 00:52 pick it was refused with 'work is left: f38-02-updated-note', a message that even sends you to a terminal. Second, without F65 the card would come back for sign-off with the old review as soon as the new ticket merged, before any review of it.
>    Action: Ticket f65-05 (developer): the card counts as 'in a round' from your Approve press until the round's review is written, and is off To sign off for all of that time. Its page shows 'More work approved' where Sign off was, with the round's tickets. Ticket f65-01 already runs the round's review.
> 2. **Cancelling the follow-up: Drop this round**: Today you can't cancel it from the dashboard. Set aside only takes a blocked ticket, an Approve can't be taken back, and the only other way out is 'sign off --force' in a terminal. I'm adding one button on the card's page, Drop this round. It sets aside every ticket of the round not yet started, and the card comes back to To sign off with its earlier review. It works even if you press it before the runner has taken your Approve, because the runner applies your requests in the order you made them. A ticket already running finishes. The dropped tickets wait under Set aside, so you can queue them again.
>    Action: Ticket f65-04 (mine): a Set aside that names a card's round. Ticket f65-05 adds the button.
> 3. **The earlier review stays on the card during a round**: F65's plan said approving a round would clear the stored review. With Drop this round, that would leave a dropped card with no review to sign off, or would trigger a review of nothing. So the review is kept. It shows on the card's page under the round plate, and it's what comes back if you drop the round. The card isn't counted as ready to sign off because it's in a round, not because its review is missing.
>    Action: D1 changed. Ticket f65-01 revised.
> 4. **Rounds no longer jump the queue**: F65's plan gave follow-up tickets priority 0. Since your 2026-10-22 rule that the board's order is the only order, a round runs in its card's place instead. That has a cost: if F38 sat 14th on the board, its round would wait behind about 50 tickets, roughly a day at 22 minutes each. If you want rounds to go first, drag the card to the top when you approve. That's one move, and it's yours.
>    Action: D5 dropped; no priority in f65-01.
> 5. **F142's sign-off is answered on F186**: My last reply promised a fix ticket here for F142's sign-off that keeps failing. Since then you planted F186, Why can't I sign off F142, which is about exactly that. Its reply is next in line, so the fix goes there and not in F65's plan. What I found: F142 was signed off on 10-28 (its git tag exists and its card says done). But the database still marks it 'review', so it shows as ready for sign-off again, and every press fails on the existing tag. Please don't press it again until then.
>    Action: Answered on F186's thread, next.
> 6. **F182 repeats this card**: F182, When I don't sign off a card and comment on it instead, asks to keep discussing a card's results and iterate before signing off. That's F65's round. It also asks for the card to show dashed orange once you've commented, and for sign-off, plan and conversation to be bundled into one item. F65 is ready and F182 is an unasked seed, so F65 is kept. Its dashed-orange and bundling parts will be answered here once its note arrives.
>    Action: Merge F182 into F65.
> 7. **The picture: To sign off and F38's page, Today and Proposed**: Drawn from F38 on 2026-10-29 at 00:40. Today: F38 sits in To sign off, its page still offers Sign off, and the refusal sends you to a terminal. Proposed: To sign off is empty. Where Sign off was, F38's page shows a 'More work approved · round 2' plate: four steps (Approved, Building, Review, Back for sign-off), f38-02 marked 'queued at the runner's next pick', and Drop this round. On a wide screen the two versions sit side by side.
>    Action: Mock-up f65-mockup/round-gap.html. Ticket f65-05 builds it.
>
> Proposals:
> - F65: off To sign off from your Approve, and Drop this round (replan)
> - More work approved: To sign off and the card's page, Today and Proposed (mockup)
> - F182 joins F65, Review rounds until you sign off (merge)
