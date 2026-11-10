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

## The lead, 2026-10-29 10:42

> Approved by the owner on 2026-10-29: approved plan/f65: queued f65-04-drop-a-round, f65-05-round-off-the-desk; changed f65-01-review-rounds

## The lead, 2026-11-04 08:08

> Merged F217 here: if i left a comment on a sign off review, i want to see…

## The owner, 2026-11-04 08:08

> From F217, merged here:
> if i left a comment on a sign off review, i want to see that it's being revised with orange dashes in the planning desk

## The lead, 2026-11-04 09:26

> Your comment does show a dash today, but in the wrong place, so this replan moves it onto the sign-off row, with a mock-up. I couldn't open the mock-up in a browser from this job, so tell me if it looks wrong.
>
> 1. **Why you don't see it being revised**: A comment on a card waiting for sign-off already gets a dashed row, but it sits at the bottom of Your answers wanted, under the same title. The row you commented on, in To sign off, stays solid and still says 'reviewed · waits for your sign-off', so it looks as if nothing happened. Proposals already switch to 'being revised' (F100, Proposals show being revised), but To sign off was never given that. You asked for this on F182, When I don't sign off a card and comment on it instead, and I said I'd answer it here. No F65 ticket covered it: that was my miss.
>    Action: Ticket f65-06 (developer): the To sign off row itself turns dashed orange, saying 'being revised' and when the reply comes, with Writing now while the lead writes it. It shows from the moment you send, and it isn't counted while it waits for the lead.
> 2. **One row per card, not two**: I went further than you asked, because dashing the row alone would leave the card in two places. F149, Retire the backlog file, is in both To sign off and Your answers wanted right now. So while such a card's comment is with the lead, or the lead has replied, its row in Your answers wanted goes. Once the lead has replied, the To sign off row turns solid and says 'the lead replied 36 s ago · reviewed, waits for your sign-off', and the card is counted once. Tapping the row opens the card with the reply. That's the first step of the bundling you asked about on F182.
>    Action: Part of f65-06 (D8). If you'd rather keep both rows, comment here.
> 3. **Bundling the rest: F210, not here**: F182 also asked whether sign-off should bundle with the plan and the conversation. A follow-up plan the lead drafts for a card still has its own row under Proposals. F210, One box per card on the desk, is already drafted and waits for your review; it joins a conversation with its proposals but keeps To sign off apart. I recommend leaving it that way until you've used this: one more row is a small cost, and merging sign-off into that box would hide what's finished, which you asked to see first.
>    Action: Nothing now. Whichever of F65 and F210 is built second keeps the one-row rule. If you want sign-offs inside F210's box, say so on F210's thread when you review it.
> 4. **No extra style for finished cards**: F182 also wondered about styling a finished card differently. I recommend not doing it: To sign off has its own green heading near the top of the desk, and only Didn't go through and Blocked tickets come before it. Another colour on the rows would need its own explanation, and you've asked for no unexplained marks.
>    Action: Nothing. Comment here if the rows still don't stand out once this is built.
> 5. **'Being revised' can overpromise, and Sign off stays**: A comment may only be a question, and then nothing gets revised: the lead answers and the row turns solid again. I'm keeping your words anyway, since proposals already say the same. Sign off also stays on the card's page while your comment waits, so you can sign off without waiting for an answer you no longer need. If you do, the row says 'signing off at the runner's next pick' and the lead's reply still arrives on the thread.
>    Action: Nothing.
> 6. **When you'll see it**: f65-06 waits for nothing, but inside a card tickets run by number, so it comes after F65's other five. F65 is behind nine other cards on the board, so it won't start soon, and you don't need to pause the factory for this replan. If you want this one sooner, tell me here and I'll make it the first of F65's tickets; you'd still drag the card up the board to bring all of F65 forward.
>    Action: Keep the order unless you say otherwise.
> 7. **The picture**: It shows your desk this morning with F149, at two moments: while the lead is writing, and once it has replied. The 08:07 reply and the card titles are real; the time on the row being written is an example. This is a mock-up of /planning, and F65's card now lists its pages for the review's before and after pictures.
>    Action: Mock-up f65-mockup/comment-dashes.html. Ticket f65-06 builds it, and I'll revise the ticket with any comments you make on it.
>
> Proposals:
> - F65: a comment dashes the sign-off row, one row per card (replan)
> - A comment dashes the sign-off row: your desk, Today and Proposed (mockup)
