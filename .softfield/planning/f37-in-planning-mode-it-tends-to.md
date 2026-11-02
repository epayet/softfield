# F37: Every number the lead writes says what it is, and links to it

The planning thread behind F37's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 19:38

> I prefer small summaries next to the number whenever mentioned, and with links when relevant

## The lead, 2026-10-26 23:03

> I've drafted a plan for F37 on the `plan/f37` branch: a writing rule for the lead, page links as a backstop, and a mock-up. Tickets pass pre-flight; nothing is queued until you approve.
>
> 1. **Why the existing rule isn't enough**: F31, When I click on approve plan, already told the planner to name a card with its title. But that rule covers cards only and the planning room only. It is also followed unevenly: in the lead's reply on F173, The board's order is the order the work runs in (26 Oct), F15 had its name but F73, F42, F26, F63 and F132 were bare. Tickets and ADRs have no rule at all. F31 also had a ticket that would have linked card numbers on the page, and it never ran: it's still set aside.
>    Action: This card takes over that part of F31.
> 2. **The lead writes a few words beside every number**: A new dated rule in your preferences file, which every lead job reads: planning replies, milestone reviews, escalations and desk notes. A card always comes with its title. A ticket or ADR gets a few words saying what it is ("ADR 29, the lead looks at a blocked ticket"). A decision like "D2" is said in words, never on its own. The planner's own instruction grows to match.
>    Action: Ticket 01, for the lead (those files are protected).
> 3. **The page adds the links, and fills in a name the lead forgot**: A writing rule on its own slips, as point 1 shows, so the planning thread backs it up. Every card number links to that card's thread. A ticket links to its ticket page. When the lead left a card bare, the page adds its name in grey, cut to about 40 letters, with the whole title on a long press. A name the lead already wrote is never doubled. ADRs get their title but no link, because no page shows ADRs yet. Your own messages stay plain text.
>    Action: Ticket 02, for a developer: it grows the function that already links /planning/ addresses.
> 4. **The mock-up: one real point from F173's thread**: Today and Proposed show the same point from the reply on F173, The board's order is the order the work runs in. In Proposed, the dashed green outlines mark the new links and the grey names the page adds. The card names come from the dashboard's own records. Some old ones are long sentences, which is why the page cuts them.
>    Action: Look at thread-names.html. Tickets 02 and 03 build what it shows.
> 5. **The review page too, after F67**: A proposal's key points get the same links. F67, Key points say what they ask of you, is about to redraw those same points, so ticket 03 waits for it to avoid the two fighting over one page.
>    Action: Ticket 03, for a developer, after F67's redraw.
> 6. **My view: linking everywhere isn't worth it yet**: You said "whenever mentioned". The board, the desk and the Overview already show names, not numbers, so they need nothing. Milestone review sheets do mention numbers, but the new writing rule (point 2) already covers them. Adding links there would mean changing how those sheets are drawn, for a small gain.
>    Action: Nothing now. If the bare numbers still bother you in reviews, plant a card for review links and it gets its own plan.
>
> Proposals:
> - Names and links beside every number (plan)

## The owner, 2026-10-26 23:49

> You mentioned mock-up I don't see it. Again ...

## The lead, 2026-10-27 13:54

> The mock-up is now listed in the proposals so it opens from this page. The plan is listed again unchanged.
>
> 1. **Why you couldn't see it: my mistake**: I drew the mock-up and committed it to this card's branch, but in my reply I listed only the plan. The page builds "Proposals from this card" from that list, so it never showed a link to the picture. It's now listed below as its own proposal, "Thread: every number says what it is". Tap it to see Today and Proposed: side by side on a wide screen, or with a switch at the top on a phone.
>    Action: Open the mock-up below. Comment on it there or here.
> 2. **Why it happened again, and the fix already waiting**: This is the "drawn, never listed" case. It happened first on F152, A done card says where its review is, on 20 Oct. The fix is written and ready: f152-02-every-mockup-is-listed makes the runner add any mock-up the lead drew but didn't list. f165-02-every-mockup-has-its-point, on F165, A point that speaks of a mock-up opens it in one tap, builds on it so an older mock-up stays listed too. Neither has run yet. f152-02 is about 25th in the queue because F152 sits 9th on the board, behind most of F132, One view of the whole factory.
>    Action: My suggestion: drag F152 to the top of the board and send. It's one small lead ticket, roughly half an hour, and it stops this from happening on every card. F165 can follow right after it.
> 3. **The plan itself hasn't changed**: Nothing in your message changes the plan. It's listed again below so its Approve button stays.
>    Action: Approve the plan and the mock-up when they look right.
>
> Proposals:
> - Thread: every number says what it is (mockup)
> - Names and links beside every number (plan)
