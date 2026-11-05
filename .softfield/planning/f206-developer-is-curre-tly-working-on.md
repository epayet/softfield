# F206: The board's developer's view counts tickets a developer has started

The planning thread behind F206's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-02 23:06

> Developer is curre tly working on f187. On the board developer view it says lead only where it's clearly dev work available

## The lead, 2026-11-02 23:25

> You're right that this is a bug: the view stops counting a developer's ticket once it starts. I've drafted one developer ticket to fix it.
>
> 1. **Why it said lead only**: The developer's view only counts tickets still marked ready. When a developer starts one, the runner marks it running, so it drops out of the count. F187, Store every time in UTC, has two lead tickets and one developer ticket, f187-02. While the local model worked on f187-02 (22:32 to 23:06, three attempts), only the two lead tickets were counted, so the card read "lead only". I found this by reading the code and the job times; I didn't catch the page during those attempts.
>    Action: Ticket f206-01 counts started tickets, with a test for each case.
> 2. **Right now it's nearly true**: f187-02 failed the checks three times (last on mypy), so it now waits for the lead. No developer can take anything on F187 at the moment, so lighting the card today would be wrong too. The card should say what happened: "developers tried f187-02 · now with the lead", faded. A blocked developer ticket gets "f187-02 is blocked". While a developer is working, the card is lit: "developers: working on f187-02 · then the lead's f187-01".
>    Action: Part of f206-01.
> 3. **The same gap in the waiting line**: A developer ticket that depends on a running developer ticket is said to wait for the lead, naming a ticket that isn't the lead's. With f170-03 running, F170, Blocked tickets, would say f170-04 waits for f170-03. It should read "1 after it".
>    Action: Part of f206-01.
> 4. **No mock-up**: The lit and faded looks stay as F146, the board's Developers only view, drew them. Only the words on a card and the legend's faded entry change, so a mock-up would show almost no difference. Ask if you want one anyway.
>    Action: Nothing.
> 5. **Who builds it, and when**: A developer: it's one small change to unprotected code, with tests to follow right beside it. The plan lands at the bottom of Planted, so it runs late unless you move it. It only corrects a view, so I wouldn't put it ahead of F170 or F187.
>    Action: Drag F206 up the board if you want it sooner.
>
> Proposals:
> - F206: the developer's view counts tickets a developer has started (plan)
