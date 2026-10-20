# Milestone F158: A card's page says what it's about: its Outcome, else your note

> **State:** ready · **Priority:** 4 · **Area:** factory
> Planted by the owner on 2026-10-20.

## Notes
milestones don't show me their descriptions, so when i click on a milestone on the board to see what it's about, i have no idea

## Why it happens (read from the code, 2026-10-20)
- A card's page (`/milestones/<key>`, `factory_dashboard/milestones.py`, `templates/milestone.html`) shows "Outcome and Done when" from the `milestones` row. That row gets them only when the card's review runs (`_record_milestone_doc` in `runner/milestone.py`); `sync_cards` in `runner/loop.py` copies only the title, state, priority and area. So every card not yet reviewed reads "Not written yet" twice, even when its doc has an Outcome: F42, The space for me to scroll on a planning proposal card, has one and its page says "Not written yet". In the database, every card from F103 to F159 has no outcome stored.
- A card not planned yet has no Outcome at all: what it's about is the owner's note (`## Notes`), and the card's page never shows it.
- Below that, seven sign-off sections each say "Not written yet" until the review, so on a phone the page is a column of empty headings before the tickets.

## Outcome
Opening a card from the board says what it's about at once, right under its header: the lead's Outcome and Done when when the card is planned, the owner's own note when it isn't yet (and folded under the Outcome once it is). The review's sections wait as one line until the review writes them.

## Done when
- F42's page shows its Outcome's bullets under the header, and its note folded as "Your note"
- F158's page (an idea, no Outcome yet) shows the note open, with "The lead writes what it will do when it plans the card."
- a card with neither shows "Nothing written about it yet." and a link to its thread
- before a review, the seven sign-off sections are one line, "The review", saying they come when the last ticket is done; once a sheet exists, they show as today
- the picture: [`f158-mockup/card-page.html`](f158-mockup/card-page.html)

## Decisions
- **D1. Read from the card's doc, not the database.** The doc is where the lead writes the Outcome and the owner's note lives, and it is current at every pick; the stored copy is taken only at review. The page reads `## Outcome`, `## Done when` (`milestone_doc` in `runner/milestone.py`) and `## Notes` (the helper f90-01 adds to `factory_dashboard/planning.py` for the thread page, F90 D2) from the doc in the project's checkout. No checkout (a URL-only project): the stored outcome, as today. No runner change, so a developer can build it.
- **D2. "What it's about" comes right after the header,** above "How it grew": the owner's question is the first thing on the page, above the fold on a phone.
- **D3. Empty review sections fold into one line.** Only while the card has no sign-off sheet at all; with a sheet, every section shows as today, so F65, Review rounds until you sign off, and F152, A done card says where its review is, build on the same page unchanged.

## Not here
- A line of the Outcome on the board's crates themselves: the board stays a field of titles; the page is one tap away. A planted card if the owner wants it.
- Storing Outcome and Done when at every pick (`sync_cards`): nothing else shows them before a review today.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | card-says-what-its-about | D | 3 | f90-01 | D1–D3: "What it's about" under the header, from the doc; empty review sections as one line |
