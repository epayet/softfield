# F220: Switching project from an inner page goes back to that tab's own page

The planning thread behind F220's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-04 23:42

> if i'm browsing a certain discussion or milestone in a project, when i switch project it stays on that planning discutssion or board ticket which is completely different, or even doesn't exist on the other side. it should go back to the overall planning or board instead

## The lead, 2026-11-05 01:22

> Plan drafted: the picker goes to the tab's own page, in one small developer ticket.
>
> 1. **Why it happens**: The picker reloads the address you are on with another project. On a card or ticket page that gives a bare "Not found" with no top bar to get back with. On a discussion it is worse: coucou's F1 opens under the same number but is a different card ("Retire docs/backlog.md"), and Softfield's F220 opens as an empty thread on coucou.
>    Action: One ticket: the picker goes to the tab that is lit, not to the same address.
> 2. **I'd apply it to every inner page, not only Planning and Board**: You named discussions and cards, but the same fault is on the others. A ticket or a run answers "Not found", a job stays on the same job under the other project's name, and a project's page ignores the picker, so nothing seems to happen. One rule covers them all: a ticket goes to Tickets, a job to Jobs, a run to Runs, a project's page to Projects. A project's page could have opened the other project's page instead, but a plain form can't put the chosen name in the address, and that isn't worth a script.
>    Action: In the ticket.
> 3. **The Milestones list stays where it is**: It lights the Board tab, so the plain rule would throw you to the Board while you compare charts between projects. Every project has that list, so it stays on Milestones. The other pages every project has (the Board, Planning, the Overview and so on) already stay, as today.
>    Action: In the ticket, as its one exception.
> 4. **It can't clash with moving the picker**: F132, The Overview shows the whole factory, moves the picker into the tab strip in a ticket still waiting. Either can land first: the new test finds the picker wherever it sits, and goes red if the move loses the new behaviour.
>    Action: Nothing for you; it's in the ticket.
> 5. **No mock-up**: Nothing on any page changes, only where the picker lands, so there is no picture to compare.
>    Action: Ask if you want one anyway.
> 6. **As planted, it would run last**: This card sits at the bottom of the board, behind 104 ready tickets, though it is a one-attribute fix you hit each time you switch project.
>    Action: After approving, I suggest dragging it up the Board or using its fast lane.
>
> Proposals:
> - Switching project from an inner page goes back to that tab's own page (plan)
