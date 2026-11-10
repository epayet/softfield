# F210: One box per card on the desk, and one reading path through its proposals

The planning thread behind F210's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-03 22:08

> Bundle a card's conversation with its proposals in one box on the desk, so I read the latest discussion and then the ADR and plan without jumping between pages. Started as F176, merged into F51 and lost when F51 closed. Drafts are on plan/f51: f51-05-one-box-per-card, f51-06-approve-plan-wakes-up and the mock-up desk-cards.html. Check them against main before reusing them.

## The lead, 2026-11-04 00:56

> Merged F214 here: Decide f31-04, "What to do now" (open proposals with their…

## The lead, 2026-11-04 00:56

> Keep the desk half of F51's draft, and add what it lacked: a reading path through each card. I drew the mock-up on the real desk from 2026-11-03 but couldn't open it in a browser from this job. One question for you, in point 2.
>
> 1. **F51's draft fixes the desk, but not the jumping**: On 2026-11-03 the desk's 11 conversations and 11 proposals were the same 11 cards, so one box takes 31 items down to 20. But the jumping is in how you read: F207's conversation is 14 of 30, and its plan is 25 of 30, so Next takes you to another card. On a phone the proposals also sit last, under Archive. The draft left the thread page as it was, so you would still have jumped.
>    Action: The plan keeps the box and adds a strip of steps on the card's pages, with a Next that stays inside the card until its last step.
> 2. **Should it be one strip of steps, or one long page? I recommend the strip**: You asked not to jump between pages, and the strip doesn't fully do that: the conversation and each proposal keep their own page, one tap apart. The alternative is everything open on one page. That costs a lot: a thread already has up to 9 points and F199's proposals add 19 key points, all on one phone scroll. It would also have two kinds of comment with two sends, Send to the lead and Send back, on one page, while every point you leave counts as agreed. The strip costs 2 small tickets where the long page means rebuilding both pages.
>    Action: Choices: the strip (as drawn, and what happens if you don't comment here), or one long page (I'd redraw the mock-up and rewrite tickets 02 and 03). Try the strip first: if the taps still annoy you, the long page can follow it.
> 3. **F214, Decide f31-04, is this same decision, so it merges here**: F214 asks to settle "What to do now" together with this card. It has no tickets or drafts, and this card is older, so this one is kept.
>    Action: The runner merges F214 into this card.
> 4. **f31-04, What to do now: delete it, and build its useful part here**: Proposals under the latest reply are the strip. Its links on names like F22 are already built (F37, Thread names). Drawing points by outcome is dropped: each point already has its action line, and F67, Key points by kind, does this for proposals. Its buttons under the reply are left out too: Approve needs the ADR-first rule and your comments, which are on the review page, and a second set would repeat them. The cost is one more tap to approve.
>    Action: Ticket 01 deletes f31-04. If you want Approve on the conversation itself, comment here and I'll add it.
> 5. **A hidden cost of Next: comments you typed get lost**: Today a comment typed on a point disappears when you leave the page. More moving between steps makes that likelier, and an unsent comment means that point counts as agreed. So typed comments now wait in that browser tab, come back on return, and the strip says "2 comments not sent". They stay in that tab only, not on another device.
>    Action: Ticket 03.
> 6. **What I changed in F51's drafts after checking them against main**: Four things. Next would have broken on proposal pages, since they would no longer be on the desk. Boxes with proposals first is gone, because F185, Your answers wanted first, asked for the newest answer first. Six dependencies become two, as only f75-01 and f108-01 are still to come. And the f51-06 fix would have brought Approve back beside Send back while you type comments.
>    Action: All four are fixed in tickets 01 and 04. The rest of the two drafts carries over.
> 7. **What stays outside the box**: Your F182 note, merged into F65, Review rounds until you sign off, asked whether sign-offs belong in the bundle. I'd keep them apart: you asked to see finished work first, and none of today's 8 sign-offs has an open conversation, so nothing doubles. F38 is the one double left: its blocked ticket and its box both show the same fix, once with Approve and once to read.
>    Action: Nothing now. F65 keeps what comes after a sign-off. If F38's double bothers you, say so and I'll add a small ticket.
> 8. **When it lands: it starts last unless you drag it**: It joins the bottom of the board, behind 55 ready cards. It changes how you go through everything else on the desk, so it pays back early. If you drag it up, the first ticket waits for F75, Archiving on approval, and F108, Desk boxes say when, and both are small.
>    Action: I'd drag it near the top once approved. Tickets 02 to 04 can run without Claude's lead, so a limit won't stop them.
> 9. **F51's leftover stays under Set aside**: F51's replan and mock-up are still listed under Set aside. Everything useful from them is copied here, so they have no further use once this plan is approved. Rejecting that replan deletes the plan/f51 branch, which F211, A plan must not get lost, may want as an example.
>    Action: Nothing now. It can wait until F211 is settled.
>
> Proposals:
> - F210 mock-up: one box per card, and one path through it (mockup)
> - F210: one box per card, one path through it, in four tickets (plan)
> - Merge F214, Decide f31-04, into F210 (merge)

## The owner, 2026-11-04 10:05

> This looks good although a small thing I tend to look at conversation for context then mock up to see result then verify the plan (rather than conversation then plan then mock-up)

## The lead, 2026-11-04 10:10

> I changed the order to conversation, mock-up, plan, on every card. The mock-up, plan and tickets are revised and pass pre-flight, but I still haven't opened the mock-up in a browser.
>
> 1. **Done: conversation, then mock-up, then plan**: This isn't a small change to the picture alone. Today the order is whatever the lead happened to list: F207, Every lead reply opens with In short, has the plan first, and F197, Plant and ask the lead comes first, has the mock-up first. So the order now comes from one rule in the code, and the desk's box, the strip of steps and Next all follow it, whatever the lead writes. On F207, Next now goes to the mock-up, then the plan, then the next card.
>    Action: Changed in the mock-up, in tickets 01, 02 and 03, and in the card's decisions as D8.
> 2. **An ADR still comes before the mock-up**: You didn't mention ADRs here, and your first note read "the discussion, then the ADR and plan". I put the ADR right after the conversation, because it is accepted first and the plan is built on it. The full order is conversation, ADR, mock-up, plan, then any merge or seed. The catch: a card with an ADR makes you read the reasoning before you see the result. Putting the mock-up before the ADR would match how you read a plan, but then you'd see a picture of something whose decision is still open.
>    Action: Stays ADR first. If you'd rather see the mock-up first there too, comment here: it's one line in the rule.
> 3. **On a phone, the mock-up step is one tap further**: Phones don't show the mock-up in the page: that step shows "Open the mock-up", which opens a new tab, and you close it to carry on to the plan. With the mock-up now in the middle of the path, you'll meet this more often. The frame was hidden on phones on purpose, because a full desktop picture doesn't fit in that space.
>    Action: Nothing in this plan. If that tab annoys you once you've used it, tell me and I'll plan a mock-up that opens within the page.
> 4. **Approve plan also shows on the mock-up's page**: It already does today, and the same press settles both the mock-up and the plan. So you can approve from the mock-up without opening the plan, the step you use to verify. I left it alone because a small card sometimes needs only the picture.
>    Action: Nothing. If you'd like the mock-up page to only point on to the plan, comment here and I'll add it to ticket 02.
>
> Proposals:
> - F210 mock-up: one box per card, and one path through it (mockup)
> - F210: one box per card, one path through it, in four tickets (plan)

## The owner, 2026-11-05 23:32

> I sent back your proposal “F210: one box per card, one path through it, in four tickets” (f210-plan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-09 16:03

> I checked the plan against main. Nothing in it was built or taken, so no ticket is renumbered or dropped. Three of main's changes touch the same pages, so I updated the tickets for them, and I redrew the mock-up on today's desk. The four tickets pass pre-flight, but I still haven't opened the mock-up in a browser.
>
> 1. **Nothing is done or taken, so nothing is renumbered or dropped**: No f210 ticket number is used elsewhere. F75, Archiving on approval (f75-01), and F108, Desk boxes say when (f108-01), are still waiting to run, so ticket 01 still waits for them. f31-04, What to do now, is still a draft, and ticket 01 still deletes it.
>    Action: Nothing.
> 2. **The desk is drawn from the stylesheet now, so the box follows it**: F81, Bring the factory theme to the older pages (f81-04), redrew the Planning room from shared styles in the stylesheet, with nothing styled inside the page itself. Ticket 01 was written before that. It now draws the box with those same row styles and adds its own beside them. Its Done when checks that no new styling went into the page.
>    Action: Ticket 01 updated. The mock-up's Today is copied from the new look.
> 3. **The mock-up shows today's desk: 11 items, 5 cards**: The desk doubles up again. Its 5 conversations and 5 proposals are the same 5 cards: F71, I suspect we might need to increase the timeouts; F211, Open plans survive a card's closing; F191, The fast lane goes first; F133, Each project gets its own card letter; and F65, Review rounds until you sign off. With one box per card it reads 6, not 11. The reading path is now drawn on F211: Next on its conversation leads to the mock-up, then the plan, then F191.
>    Action: Mock-up redrawn.
> 4. **F65, Review rounds until you sign off, also makes one row per card**: F65's replan, waiting for your Approve, moves a finished card's conversation into its To sign off row (f65-06). With both plans as they were, such a card's proposals would have stayed behind in Your answers wanted. Now a card's proposals go into whichever row holds its conversation, so the two plans agree in either order. F65 is higher on the board, so it will most likely land first.
>    Action: Added as D9. Ticket 01 covers it.
> 5. **F224, Approve first, adds a second button that must wake up too**: f224-02 adds an Approve first fold beside Approve plan, and it is also greyed out while the ADR waits. Ticket 04 only woke up Approve plan, so Approve first would have stayed grey. Ticket 04 now redraws both from the same poll, and waits for f224-02 so it has the fold to work on.
>    Action: Ticket 04 updated and now waits for f224-02.
> 6. **F207, In short, sits under the strip on a review page**: f207-02 puts an In short plate under a review page's header. The strip takes the old tabs' place, so it comes first and the plate under it. On a conversation the In short plate is part of the reply, and the strip comes after the reply.
>    Action: Ticket 02 says where each goes.
> 7. **Not checked in a browser**: This job can't open pages, so I haven't seen the new picture drawn.
>    Action: If it looks wrong, tell me here.
>
> Proposals:
> - F210 mock-up: one box per card, and one path through it (mockup)
> - F210: one box per card, one path through it, in four tickets (plan)

## The owner, 2026-11-09 23:05

> I sent back your proposal “F210: one box per card, one path through it, in four tickets” (f210-plan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-09 23:08

> I checked again: nothing on main has touched this plan since this afternoon's check, so it comes back unchanged.
>
> 1. **Nothing changed since this afternoon's check**: Since the 16:00 check, main has merged F228, The Overview loads faster (f228-01), approved the plans of F71, F230, F232 and F234, and taken in F235, F236 and F237. None of them touches the desk, the thread page, the review page or their scripts. The tickets this plan waits for or works around are where they were: f75-01, f108-01, F207's f207-02 and F224's f224-02 are still waiting to run, and F65's f65-06 still waits for your Approve. No f210 number is taken, and all four tickets pass pre-flight again.
>    Action: Nothing. The plan and mock-up are listed again, unchanged, so you can approve them.
> 2. **This second check cost one more reply**: The same check had already run at 16:00, and nothing had changed since, so this reply cost one more Opus job for no new result.
>    Action: Nothing to change. If the review page said the plan looked stale when you pressed it, tell me here and I'll look at why.
>
> Proposals:
> - F210 mock-up: one box per card, and one path through it (mockup)
> - F210: one box per card, one path through it, in four tickets (plan)
