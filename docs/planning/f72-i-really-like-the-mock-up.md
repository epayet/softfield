# F72: I really like the mock up feature, especially to see…

The planning thread behind F72's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-09 09:27

> I really like the mock up feature, especially to see before/after change. This should be the default for frontend features

## The lead, 2026-10-09 09:29

> I agree with you and drafted it as a plan: Today and Proposed views of the same page by default, plus one lead ticket. I didn't do it in exactly the form you suggested; my three changes are below.
>
> 1. **Yes, make it the default, with a clear line for when it applies**: A mock-up becomes the default for any card that changes what a page shows or how it's laid out. That covers the dashboard and the app: a new view, something added, moved or removed, or a new state or colour. I'd leave out three cases: wording-only changes, a bug fix that puts a page back the way it was meant to look, and work with nothing on screen. Each mock-up costs one more Opus planning turn, and for a one-word change a single line tells you as much. When I skip a mock-up on a card that does touch a screen, I'll say why in a point, and you can ask for one.
>    Action: F72 D1 and ticket f72-01
> 2. **Before and after, flipped with one tap, from the real page**: Each mock-up has a Today / Proposed switch at the top. On a phone you flip between two pictures of the same size instead of scrolling from one to the other. On a wide screen they sit side by side. The risk is that 'Today' gets redrawn from memory and doesn't match what you actually see. So it is copied from the live page's template and CSS, with real values from the queue and the cards. 'Proposed' outlines each change and adds a short note. F17's top bar mock-up already had a 'Today, for comparison' section, and this makes that standard.
>    Action: F72 D2
> 3. **Mock-up and tickets in the same reply**: Today the rule is to agree on the mock-up first and write the tickets after, which takes a round more per card. I recommend sending both in the same reply, with each UI ticket naming the mock-up as the picture to build. If your comments change the mock-up, I revise the tickets in the same turn. The cost: when a mock-up changes a lot, the first tickets are wasted work, but nothing gets queued before you approve. The alternative is to keep the mock-up first, tickets after.
>    Action: F72 D3; say if you prefer mock-up first
> 4. **Where the rule goes: the planner's brief, not an ADR**: This is one paragraph in the planner's brief, one line in lead.md and a wider 'Mock-ups before UI tickets' rule in owner.md, so terminal sessions follow it too. An ADR felt like too much ceremony for a rule that small. It's one small lead ticket, test-first on the brief.
>    Action: Ticket f72-01-mockup-by-default (lead, difficulty 2)
> 5. **Later: the real 'after' at sign-off**: A mock-up shows the intended result, not what actually got built. Once a frontend card is done, a screenshot of the live page next to the mock-up's Proposed view would show whether the build matches. That needs a headless browser in the runner, so it's a separate piece of work. I've noted it under 'Later' in F72's doc.
>    Action: The roadmap, if you agree
>
> Proposals:
> - Before/after mock-ups by default for frontend cards (plan)
