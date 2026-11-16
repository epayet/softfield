# F243: Pull a fast lane lever back before the runner takes it

The planning thread behind F243's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-14 12:40

> Plan this card.

## The lead, 2026-11-16 19:23

> I've drafted a plan for F243: a lever that has been pulled can be pulled again to take the request back before the runner sees it. It comes with a mock-up and three tickets, which pass the ticket check.
>
> 1. **Why you can't undo it today**: Once you pull the Fast lane lever on a card's page, it locks with its dashed edge until the runner's next pick, which can be most of an hour away. Even if it didn't lock, a second pull wouldn't help: the runner applies every open lever request in order. 'In' then 'out' would make two commits on main and leave you where you started.
>    Action: The plan below fixes both: the lever stops locking, and the runner only acts on your latest pull.
> 2. **The runner acts on your latest pull only**: For each card or switch, the runner applies only the newest open request; any older one is dropped, the way an older board order already is. If the newest pull asks for what is already true, the runner changes nothing, makes no commit, and logs 'taken back: F199 stays out of the fast lane'. No new kind of request: the pull-back is an ordinary lever request.
>    Action: Ticket f243-01, for the lead, because runner/ is protected. Tests first.
> 3. **The lever undoes at once**: The lever is no longer locked while your pull is on its way. First pull: knob halfway, dashed edge, as today. Second pull: it goes back to plain at once and stays plain after a reload. A third pull asks again. While it is on its way, holding the pointer over it shows 'pull again to take it back'.
>    Action: Ticket f243-02 for a developer. The picture is .softfield/cards/f243-mockup/take-back.html.
> 4. **The board and the Overview follow the pull-back**: After a pull-back, the board's dashed 'fast lane · on its way' label is gone. The card also leaves the Overview's 'Fast lane:' line and is no longer marked on its way in Next in line. A card already in the lane that you pull out and back in keeps its plain 'fast lane' label.
>    Action: Ticket f243-03 for a developer.
> 5. **The 'use reserve' levers get the same fix**: Your note is about the fast lane, but the two 'use reserve' levers on the Overview's allowance lock in exactly the same way. It's the same code and the same tests, so fixing them too costs almost nothing. Leaving them out would mean two levers that look the same and behave differently.
>    Action: Included in f243-01 and f243-02. Say so if you want them left out.
> 6. **Approve first stays as it is**: When you approve a plan with 'goes first' (F224, Approve first), that is an approval, not a lever pull, so this card doesn't make it undoable. Once the approval lands, the card's own lever takes it out of the lane, which works even before this card. To undo an approval before the runner takes it would need its own card.
>    Action: Nothing. Plant a card if you want approvals to be undoable too.
> 7. **Where it goes and how long**: Three tickets: one for the lead, then two small developer tickets that can run side by side. That's about an hour and a half at the recent pace. The card goes where you place it on the board.
>    Action: Nothing to do: drag the card where you want it on the board.
>
> Proposals:
> - F243: pull a fast lane lever back before the runner takes it (plan)
> - F243 mock-up: pulling the fast lane lever back (mockup)
