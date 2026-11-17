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

## The lead, 2026-11-16 20:59

> Approved by the owner on 2026-11-16: approved plan/f251: queued f251-01-uptime-in-the-top-bar; F251 goes last on the board

## The owner, 2026-11-17 08:04

> The text overflows on the left on mobile I can't see the beginning

## The lead, 2026-11-17 12:11

> I found why the start of the text is cut off on your phone, and I've drafted a fix as one small ticket for F251, Show how long the computer has been on in the top bar. It passes the ticket check, and it runs once you approve the replan.
>
> 1. **Why the beginning is cut off**: When you tap the dot on a phone, the status words open in a box under the top row. The box is lined up on the right edge of the status, and the status sits second in the row, just after the SoftField name, close to the left of the screen. So a wide box can only grow leftwards, past the screen's edge. The 'Computer on … · since …' line made the box wider, so the overflow is easy to see now. A long status alone, like 'Paused by you since 19:28 · coaster-ranker', could already cut off.
>    Action: Fix it with ticket f251-02.
> 2. **The fix**: On a phone, the box will start from the left edge of the top bar instead, and a long status will wrap onto a second line. Nothing changes on a wide screen. A test on a phone-sized screen checks that the whole box stays on screen. It's a small style change, so a developer builds it.
>    Action: Ticket f251-02-phone-words-stay-on-screen.
> 3. **The mock-up had the same fault**: The mock-up's phone picture copied the dashboard's old placement, so its box hung off the left too. I've corrected the picture to match the fix. Nothing else in the design changes.
>    Action: Nothing.
> 4. **Pausing first isn't needed**: This adds a new ticket and changes none that are waiting, so the line can't start the wrong thing while we talk. No pause is needed. Approving puts the fix in the queue.
>    Action: Approve the replan.
>
> Proposals:
> - F251, Show how long the computer has been on in the top bar: the phone's status words stay on screen (replan)
> - F251 mock-up: how long the computer has been on, in the top bar (mockup)
