# F114: Notifications only for what needs me, one per bundle, opening its page

The planning thread behind F114's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-13 18:07

> I want to be notified only for things that need my attention: a new feature to sign off, an answer to my question/threads, a new proposal. Is this currently the case? I don't want to be notified every time a ticket is finished for example. When mockups/proposals/adrs come in bundled, I just need one notification

## The lead, 2026-10-13 18:10

> F114's plan is drafted on `plan/f114`: the card's doc and two developer tickets, which pass pre-flight when checked by name.
>
> 1. **A finished ticket never notifies you**: Nothing in the code notifies when a ticket finishes or merges. Each notification is a new "Needs you" item, plus one when all the work is done.
>    Action: Nothing.
> 2. **A bundle from the lead is already one notification**: The runner stores one item per thread for each lead reply, so a mock-up, a plan and an ADR arriving together are one notification. A sign-off is one per card.
>    Action: Nothing.
> 3. **Seven other things notify you today, and I would keep them all**: They are: a decision (an ADR from an escalation), a blocked or escalated ticket, a review that stopped, Claude's reserve or 5-hour share asking for your choice, the runner stopped mid-job, tickets waiting with no runner, and all the work done. Each one stops work or waits for you; "all the work done" is the moment to plan more. Once F106, where do blocked tickets go for me to review, has landed, a blocked ticket will notify twice: at the block, and when the lead's look arrives with a fix. I keep both because the look can wait hours for Claude's allowance.
>    Action: Nothing changes; the list is decision D4 of the plan. Say which ones you want silenced.
> 4. **A notification doesn't say what it is about**: Every one is titled "Needs you". A sign-off's body is its test steps or the review's file path, without the card's name; a reply's says "F114", not the title. Proposed: "The lead replied: <card title>" with "2 proposals to review" or "Your answer is wanted", "Ready for your sign-off: <card title>", and so on. The full table is in the card's doc.
>    Action: Ticket f114-01 (developer): the dashboard words each notification from the item's kind and its card. Nothing changes in the runner.
> 5. **A tap doesn't open the right page**: Today a tap brings forward whichever dashboard page is open, or opens the Overview. Proposed: a reply opens its card's thread, a sign-off its card's page, the rest the Overview.
>    Action: Ticket f114-02 (developer).
> 6. **Several things at once are several notifications**: A review's verdict can open three items in one go (a decision, a blocked ticket, the review's stop), which gives three notifications. Proposed: whatever is new in the same 5-second look is one notification, "3 things need you", with their titles, and a tap opens your desk.
>    Action: Ticket f114-02, the same one as the tap.
> 7. **The real limit: nothing reaches you with the dashboard closed**: Notifications only come while a dashboard page is open. A phone freezes a background page after a few minutes, and what arrived while every page was closed is never notified; it only shows on your desk. So the plan above makes notifications right, not present. Reaching a locked phone needs either a small ntfy server on this machine with its app on your phone, or https with a certificate installed on each device. Both install something, so it starts as an ADR. I recommend keeping it out of this card and doing it next, as a card of its own: it is the part that makes "watched from a phone" true.
>    Action: Your choice: (a) I draft that ADR on this thread now, recommending ntfy; (b) it stays on the roadmap for later. I recommend (a) once this plan is approved.
> 8. **No mock-up for this card**: No dashboard page changes: only the phone's and the desktop's own notifications do. Their words are the table in the card's doc (decision D1).
>    Action: Nothing, unless you want a picture of the notifications.
> 9. **The second ticket waits for two others**: f114-02 changes the notification's title and removes the old data that f95-01 (F95, overview currently says I have 2 things to sign off) and f12-05 (F12, Turn on notifications) both test. It runs after them. Both are ready today; f12-05 is at priority 100, like this card.
>    Action: Nothing: the dependency is in the ticket.
> 10. **Another card's draft fails the ticket check**: The check of every draft in tasks/later reports f9-12-fix-the-desktop-test-does: it lists only tests and doesn't say `tests_only: true`. It isn't this card's, so I didn't touch it. F114's two tickets pass when checked by name. I don't know whether Approve checks every draft or only this plan's; if it refuses this plan because of f9-12, that is the cause.
>    Action: Fix: add `tests_only: true` to f9-12 on the thread of F9, where the draft belongs; one line.
>
> Proposals:
> - Notifications say what they are, come once, and open their page (plan)

## The owner, 2026-10-13 19:36

> I sent back your proposal “Notifications say what they are, come once, and open their page” (f114-plan).
> - On its key point 6 (Not in this card: notifications with the dashboard closed): Ah so I need to have a tab on the planning page to get notified? What if I'm browsing overview or board?

## The lead, 2026-10-13 19:36

> The plan itself is unchanged; I only made the doc say plainly that any dashboard page notifies, and listed the plan again so you can approve it.
>
> 1. **No: any dashboard page notifies you, not only Planning**: The Overview, the Board, Planning or any other page will do. Every page loads the same notification script and looks every 5 seconds for something new, so you are notified wherever you are browsing. Two tabs open at once don't notify twice: what was already seen is remembered per browser. My wording "with the dashboard closed" meant no dashboard tab open at all, or the phone locked long enough for it to freeze the page.
>    Action: Wording only: the card's doc now says "any dashboard page" in what happens today and in how to test. The tickets don't change.
> 2. **Still open: notifications with no dashboard tab open at all**: That part is unchanged and still outside this card: reaching a locked phone, or a computer with no dashboard tab, needs either a small ntfy server on this machine with its app on your phone, or https with a certificate installed on each device. Both install something, so it starts as an ADR.
>    Action: Your choice: (a) I draft that ADR on this thread once this plan is approved, recommending ntfy; (b) it stays on the roadmap. I recommend (a).
>
> Proposals:
> - Notifications say what they are, come once, and open their page (plan)
