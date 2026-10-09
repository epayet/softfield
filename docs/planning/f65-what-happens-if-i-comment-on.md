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
