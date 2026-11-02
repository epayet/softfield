# F158: A card's page says what it's about: its Outcome, else your note

The planning thread behind F158's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-20 09:10

> milestones don't show me their descriptions, so when i click on a milestone on the board to see what it's about, i have no idea

## The lead, 2026-10-20 11:19

> I've drafted a plan for F158, with a mock-up of the card's page and one developer ticket. The cause is in the code: a card's Outcome only reaches the page once its review runs, and the page never shows your own note.
>
> 1. **Why the page says "Not written yet"**: The page that opens when you tap a card on the board shows the Outcome kept in the database. That copy is only made when the card's review runs. So every card not yet reviewed says "Not written yet", even when its doc has an Outcome: F42 (The space for me to scroll on a planning proposal card) has one, and its page shows none. Cards F103 to F159 have no Outcome stored at all. A card not planned yet has no Outcome, only your note, and no page shows that note.
>    Action: Ticket f158-01 reads the Outcome and your note straight from the card's doc each time the page opens.
> 2. **"What it's about" right under the header**: A new panel sits first on the page, above "How it grew", so it shows without scrolling on a phone. A planned card shows what the lead said it will do and its Done when, with your note folded under them. An idea shows your whole note, open, plus "The lead writes what it will do when it plans the card."
>    Action: Mock-up card-page.html, built by f158-01.
> 3. **Seven empty review sections become one line**: Before a review, the page shows seven headings that each say "Not written yet", and they push the tickets far down. Until a review exists they become one line: "The review comes when the last ticket is done." Once the review is written, the sections show as they do today, so F65 (Review rounds until you sign off) and F152 (A done card says where its review is) aren't affected.
>    Action: Part of f158-01.
> 4. **Not on the board's cards themselves**: I'd keep the board to titles. An Outcome line on every card would make the columns several times longer on a phone, and the description is one tap away. If you'd still like a one-line summary on each card, say so and I'll add it.
>    Action: Nothing for now.
> 5. **It waits for F90's note ticket, and fixes a slip in it**: F90 (Editing seeds: show the whole note) already has a ticket that shows your note on the planning thread page. F158 reuses its code rather than copying it, so it runs after that ticket. F90's ticket says the docs live in the wrong folder (`milestones`; it is `cards`). Its tests could pass while the real page shows nothing. My ticket checks the real folder and corrects F90's code if needed. It's the same page and the same rule, so this isn't a repeat of F90; the two cards stay separate.
>    Action: Handled in f158-01; nothing for you to do.
> 6. **Built by a developer, about an hour**: It only touches the dashboard page and follows F90's example, so it goes to a developer. No change to the runner is needed. One ticket, about an hour of factory time once F90's ticket is done.
>    Action: Approve to queue it.
>
> Proposals:
> - A card's page says what it's about (plan)
> - Card page: What it's about (mockup)
