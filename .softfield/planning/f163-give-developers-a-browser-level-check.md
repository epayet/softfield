# F163: A browser check for htmx parts: swap, then post again

The planning thread behind F163's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 09:34

> I've drafted F163's plan. The note says two of M1's blockers would have failed the check, but I found only one would: the other was a timing bug between two threads, which no browser test can see. The same problem has come back in four of Travel companion's five later reviews, though. So the case for the check is stronger than the note makes it.
>
> 1. **One of M1's two blockers, but four more since**: Of M1's two blockers, only the first (Undo worked only once) would fail a 'swap, then post again' check. The second (Try again woke the worker before its save was finished) was a timing bug between two threads, and no browser test can see that. But the same kind of bug came back after M1 in four of Travel companion's five later reviews: F1 (a row came back without its chips), F3 (Forget then Undo), F4 (a count line that never showed; three fix rounds, about an hour, and the bug stayed) and F6 (a form that broke when posted back). Each was found by the review, never by a test. The developer notes asking to 'test after a second swap' were already there for all four: a note the developer can't run doesn't hold.
>    Action: Recorded in the card's 'What we know'.
> 2. **A real browser, not a simulated swap**: A cheaper option would be Python code that applies the swap to the test's HTML. It would catch M1's bug and those in the F1, F3 and F6 reviews, but not F4's, which was a script reacting to typing. Playwright runs the real htmx and the real scripts for about a second a test. It needs no server either: each request the page makes is answered by Django's test client, the way Softfield's own dashboard tests already work. One known snag: Django refuses database calls inside Playwright, so the browser tests switch that check off for themselves only.
>    Action: Card decisions D1 and D2.
> 3. **Travel companion builds it, on its own board**: The test setup, the first test (undo two chips, one after the other) and the worked example belong in Travel companion's code, and from here I can't add work to its queue. Its lead should build the first one, because it's a new kind of work. Please paste this into the Plant box on Travel companion's Planning page: "Give developers a browser check for htmx parts, as Softfield's F163 decided: Playwright loads the page through Django's test client (no server), with the real htmx and notes.js. The lead builds the setup and a first test that undoes two chips one after the other, then adds it to the worked examples. Page tickets then ask for one test that makes the second request."
>    Action: You plant it on Travel companion's board; its lead plans it there.
> 4. **Not a factory feature for every project yet**: Shipping this setup with every new project from Softfield's templates sounds tidy, but only one project uses htmx with Django. I'd wait for a second one before making it general.
>    Action: Nothing now; card decision D4.
> 5. **Softfield's part: ask about the second request**: Two more of that review's factory ideas are Softfield's own and help every project: ticket-writing makes a page ticket name the second click in its Done when, and the checkpoint checks each swap the code adds against what its view sends back and looks for a test that makes the request twice. One small lead ticket covers both, and it passed the ticket check.
>    Action: Ticket f163-01-second-request-in-briefs (lead, difficulty 2).
>
> Proposals:
> - F163: ask about the second request; the browser check goes to Travel companion (plan)
