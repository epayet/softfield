# F97: Needs you steps aside: Now first, a box of desk counts at the bottom

The planning thread behind F97's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 23:56

> Plan this card.

## The lead, 2026-10-27 04:06

> The plan follows your idea: Now goes first, and Needs you becomes a box at the bottom. I'm pushing back on one part: anything that stops the line stays near the top.
>
> 1. **The desk line repeats the Planning tab's count**: You're right. Today Needs you holds a single line on softfield: "25 things wait for you on your desk", plus three titles. The Planning tab already shows that 25, and on a phone the line fills the first screen above Now. So Needs you moves to a box at the bottom of the Overview. Each project's desk becomes one plate with its count, and a tap opens that project's Planning room. The titles go, because the desk lists them.
>    Action: Ticket f97-01, built from the mock-up's Proposed side.
> 2. **Not everything in Needs you is on the desk**: Needs you also holds things that are on no desk: the runner stopped mid-job, tickets waiting while the runner is idle, a check failing on main. At the bottom of a phone page you would miss these, and they explain why Now looks wrong. I recommend they show as a "Line stopped" strip at the top of Now. The calmer items (Claude's allowance questions, an ADR, a review that stopped) go in the bottom box with the desks. The other options are to put everything at the bottom, as your note says, or to have the box jump to the top only while the line is stopped.
>    Action: Built as recommended in f97-01. Tell me if you want everything at the bottom instead.
> 3. **Other projects' desks keep a place on the Overview**: The Planning tab counts only the project you've picked. Right now travel-companion and coucou have 1 item each on their desks, which only the Projects page shows. Once F132 (One view of the whole factory) makes the Overview cover every project, the bottom box shows one plate per project: 25 softfield, 1 travel-companion, 1 coucou.
>    Action: Part of f97-01.
> 4. **It follows F132, One view of the whole factory**: This isn't a repeat, but it changes the same panel. F132's ticket f132-02 rebuilds Needs you with one desk line per project, each with its top three titles, and f97-01 then shrinks those lines to counts. Building the titles first and then removing them wastes a few lines of work. Avoiding that would mean pausing the factory and replanning F132, which costs more. So f97-01 waits for f132-02 and f132-04, which edits the same template, and replaces F132's desk line (its D6).
>    Action: Nothing to do. The card's D2 records it.
> 5. **Mock-up**: Today is the live Overview of 2026-10-27. Proposed is drawn after F132: Now is first, then the queue, the allowance, the floor and While you were away, and Needs you comes last with three desk plates and travel-companion's two open allowance questions. Below that is a drawn example of the "Line stopped" strip, which isn't real data: nothing stops the line today.
>    Action: Look at .factory/cards/f97-mockup/overview.html.
>
> Proposals:
> - F97: Needs you steps aside on the Overview (plan)

## The owner, 2026-10-27 08:07

> On point 5: i don't see the mockup, once again...

## The lead, 2026-10-27 18:50

> The mock-up was on the branch, but nothing pointed the page at it. It now has its own proposal, so it opens from this thread. The plan is unchanged.
>
> 1. **Why you didn't see the mock-up**: The file was drafted and saved on F97's plan branch (.factory/cards/f97-mockup/overview.html). The page only shows a mock-up when a proposal points at it, and my last reply had only the plan, which points at the card's doc. That was my mistake. Two ready cards remove the cause for every thread: F165, A point that speaks of a mock-up opens it in one tap (f165-02), and F152's f152-02, which lists every mock-up of a plan. Until they're built, every reply with a mock-up must also list it as its own proposal.
>    Action: The mock-up is now listed below as its own proposal. Open "F97 mock-up: Needs you steps aside" under Proposals from this card.
> 2. **What the mock-up shows**: Today is the live Overview of 2026-10-27, with Needs you on top holding the desk line (25 items and three titles). Proposed puts Now first, then the queue, the allowance, the floor and While you were away. Needs you comes last as a box: one plate per project's desk (25 softfield, 1 travel-companion, 1 coucou), then travel-companion's two open allowance questions. A drawn example below it shows the "Line stopped" strip at the top of Now. On a phone, flip between Today and Proposed with the switch; on a wide screen they sit side by side.
>    Action: Comment on the mock-up's points if anything should change. The ticket follows it.
>
> Proposals:
> - F97 mock-up: Needs you steps aside on the Overview (mockup)
> - F97: Needs you steps aside on the Overview (plan)

## The lead, 2026-10-29 09:55

> Approved by the owner on 2026-10-29: approved plan/f97: queued f97-01-needs-you-steps-aside

## The owner, 2026-11-24 08:06

> There is horizontal scrolling issue on mobile on overview page now, is this from here?
> The reserve questions I can't do anything about them why are they still there

## The lead, 2026-11-24 08:29

> Neither problem is this card's work: the sideways scroll comes from another card's styles, and the reserve questions are left over from an old allowance setting. I've drafted a fix for each on this card, and both run once you approve.
>
> 1. **The sideways scroll comes from F210's strip, not from this card**: The cause is in the code, not on screen: I couldn't take a phone picture from here, so the fix ticket checks it at 390 px first. On 10 November, F210 (One strip of steps) styled the steps strip on a card's thread with rules named for every list of that type. The Overview's While you were away and Needs you lists use the same type, so they got those styles too. Each ticket link became a tall, uppercase button that can't wrap, and a name like f262-02-archive-on-the-projects-page is wider than a phone. F97's own change only added boxes and plates that wrap.
>    Action: Ticket f97-02 (developer): limit F210's styles to its own strip, and add a test that the whole Overview doesn't scroll sideways on a phone. No mock-up: it brings back the look the page already had.
> 2. **Why the reserve questions never go away**: You're right that there's nothing to do about them. They are travel-companion's two items from 23 October, asking you to turn the reserve back on. Only a request from travel-companion itself can clear them, and the Overview's levers act on the project you have picked. Their words are also out of date: since ADR 50, a lever that is off only means lead tickets go after the developers' tickets past the mark. Nothing waits for you, so the question asks for nothing.
>    Action: Ticket f97-03 (lead, because it changes the runner): when a lever's 24 hours end, it turns off quietly, with no Needs you item and no notification. When the runner next starts, it clears every open reserve question, including these two.
> 3. **This reverses one of your earlier rules**: On 4 October you asked for the runner to ask you again when a lever turned itself off (ADR 22's flagged note). f97-03 stops that. The note in ADR 22 stays, with one line under it saying it no longer applies. You can still see whether each lever is on, beside the allowance on the Overview. Approving this plan settles it; tell me if you'd rather keep the question for the week's lever only.
>    Action: Part of f97-03.
> 4. **Sign-off waits for these two**: F97's review is waiting for your sign-off, and approving this plan adds two tickets to the card. Nothing else depends on them, so they run in F97's place on the board. Sign off once both are merged: the Overview shouldn't scroll sideways, and the box should hold only the desk plates. You don't need to pause the factory, because no running work is affected.
>    Action: Approve, then sign off after f97-02 and f97-03 merge.
>
> Proposals:
> - F97: no sideways scroll on a phone, no reserve questions (replan)
