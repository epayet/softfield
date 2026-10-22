# F171: Each card once on the board, and fix tickets named after what they fix

The planning thread behind F171's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-22 08:42

> there are dupliacted tickets on the travel companion board. also the ticket name picking looks fishy and buggy

## The lead, 2026-10-22 08:48

> I found both faults, and they come from the runner, not from the travel-companion cards. I drafted three tickets for them on `plan/f171`; all three pass the ticket check.
>
> 1. **Why travel-companion's board shows F4 and F2 twice**: Each card has only one doc. But the F4 tickets and the F2 ticket name their card by its short key (`milestone: f4`) instead of its full one. When the runner records a ticket it uses the key exactly as written, so it made a second, empty milestone row called just `f4` next to the card's real row. The board draws a card for every row, and it tells cards apart by `F4`, so both copies show the same thing. That's why F2 shows twice as "F2" with no title, and why its README ticket is missing from the real F2 card, "A README with the commands to start Tabi". The milestones list shows the same two empty rows.
>    Action: Ticket f171-01 (lead): the runner files a ticket under its card's full key, wherever it reads one. On its next sync it also moves the empty rows' tickets and jobs onto the real cards and deletes the empty rows. That repairs travel-companion's board without anyone touching it.
> 2. **Softfield's own board has the same fault**: A planner job on a card that was merged away leaves an empty row named by its short key. So "F107" sits in Planted with no title, and F29 and F44 have empty rows too.
>    Action: Ticket f171-02 (developer): the board and the milestones list skip a milestone row that has no card and no tickets. It doesn't wait for ticket 01.
> 3. **The ticket names that look buggy**: A fix ticket filed at a checkpoint takes its name from the first four words of the finding's sentence, so the name stops mid-phrase: `f1-14-fix-the-been-test-does`, `f114-09-fix-notification-tests-do-not`. My plan is to name it after the ticket it fixes instead: `f1-14-fix-restamp-been-and-undo-tests`. You can read straight away which work it repairs. Tickets that already exist keep their names, because renaming them would break the links to them. If by "name picking" you meant something else, such as card names taken from the first words of your note, typos included, tell me here.
>    Action: Ticket f171-03 (lead).
> 4. **No mock-up for this card**: These changes only bring the board back to the look it was meant to have: each card once, with its title. The new names are wording only.
>    Action: Nothing.
> 5. **Priority 3 for all three tickets**: A board that shows wrong cards misleads every look you take at it, so I put all three at priority 3, next to the notification work. They are small: about 2 to 3 hours of work in total.
>    Action: Drag them on the board if you want them elsewhere.
> 6. **Another card's draft would fail its approval**: The ticket check also flagged `f9-12-fix-the-desktop-test-does`, a draft under F9 in `.factory/tasks/later/`. It changes only tests but isn't marked as a test-only fix, so approving that plan would be refused.
>    Action: I'll add `tests_only: true` to it on F9's own thread. Nothing changes here.
>
> Proposals:
> - F171: each card once on the board, and fix tickets named after what they fix (plan)

## The owner, 2026-10-22 08:54

> On point 3: i also meant that i think at some point it was confused if it should pick m or f. perhaps it doesn't matter that much anyway

## The lead, 2026-10-22 08:55

> I found why the letter got mixed up, added a fourth ticket for it to the F171 plan, and all four tickets pass the ticket check.
>
> 1. **Why travel-companion went M1, then F1 to F9**: You're right that it got confused. A card's letter comes from its area: factory cards get F, product cards get M. A note from the one-box Plant field doesn't say which area it is, so the runner always makes it a factory card. M1 was set up with its area, but every card you planted after it became an F, even product work like "Ask or tweak: a note on each idea card". I changed some of them to product afterwards, but the letter stayed. It doesn't break anything. It does make the board's Factory and Product filter wrong on that project, and the next product card would get F10 instead of M2.
>    Action: Ticket f171-04 (lead): a note planted without an area takes its project's area. Every project defaults to product, except softfield, which stays factory. That's about half an hour of work.
> 2. **Existing keys keep their letter**: Renaming F4 to M2 would mean changing the card's file name, its conversation, its plan branch and every ticket name. That's a lot of risk for one letter. From now on only new cards get the right letter.
>    Action: Nothing. If you still want travel-companion's cards renamed, say so here and I'll plan it as its own card.
>
> Proposals:
> - F171: each card once on the board, fix tickets named after what they fix, and the right key letter (plan)
