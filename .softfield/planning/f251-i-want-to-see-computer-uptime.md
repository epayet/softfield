# F251: Show how long the computer has been on in the top bar

The planning thread behind F251's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-14 13:08

> I want to see computer uptime on the dashboard curious to see how long the computer has been on

## The lead, 2026-11-16 19:34

> I've drafted the plan: one small developer ticket that puts "On 6 d 4 h" in every page's top bar, with a mock-up (`.softfield/cards/f251-mockup/uptime.html`). The pre-flight check passes my ticket; it flagged two older drafts from F9's tickets, which aren't part of this card.
>
> 1. **Where it shows**: Nothing on the dashboard shows uptime today. I'd put it in the top bar so you see it on every page. On a wide screen it's a small 'On 6 d 4 h' plate after the status, and hovering it says since when. On a phone the top row is already full (the logo, the dot, the project and the theme switch), so the plate hides there. Instead, tapping the dot, which already shows the status words, adds a second line: 'Computer on 6 d 4 h · since Tue 10 Nov 15:42'. The other choice is a panel on the Overview, but that would take room from 'what's running', which you want at the top.
>    Action: Ticket f251-01, built from the mock-up's Proposed.
> 2. **It stays fresh and costs nothing extra**: The time travels with the status, which every page already refreshes every 5 seconds, so an open page never shows an old number. It adds no new request and no new library. On Linux it reads the system's own counter; on a Mac it asks the system for its start time. If neither works, the plate isn't shown and the page still loads.
>    Action: Settled in the card's Decisions (D1, D2).
> 3. **What 'on' means, and which computer**: It counts from the computer's last start, and time asleep counts as on. That's what the system reports, and it matches what you care about here: when you last restarted. It's the computer the dashboard runs on, which is also the runner's. If LM Studio runs on a different machine, that machine's uptime won't show. Say if you'd like that one too; it would need its own reading.
>    Action: Nothing, unless you want the LM Studio machine's uptime too.
> 4. **A developer builds it**: It's a small ticket: a new file outside the protected folders, plus the status's own template and CSS, following how the status is drawn now. So it goes to a developer, not the lead. It touches only the status area, so it won't clash with F132's move of the project picker into the tabs. Its place in the queue comes from F251's place on the board.
>    Action: Approve the plan, then drag F251 on the board to where you want it.
> 5. **Pictures for the review**: The card doc lists `/` under 'Before and after'. The review will take a picture of the Overview's top bar there and check it against the mock-up.
>    Action: Nothing.
>
> Proposals:
> - F251, Show how long the computer has been on in the top bar (plan)
> - F251 mock-up: how long the computer has been on, in the top bar (mockup)
