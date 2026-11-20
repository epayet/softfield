# F275: A project started from the Projects page goes first, not last

The planning thread behind F275's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-19 16:04

> a project created by web interface takes first place rather than last place. i usually want it now, so it should be first rather than last

## The lead, 2026-11-19 16:07

> I drafted a small plan for F275: a project started from the Projects page goes first in the order, and a mock-up of the change. Both tickets pass the ticket check; nothing is queued until you approve.
>
> 1. **Why a new project comes last today**: When the runner adds a project to the database, it puts it after the last one. A project you start from the page then waits behind Softfield's 143 ready tickets until you drag it up and send. Your Projects page shows exactly that right now: duck-ascii-test is sixth in the database, and the order you sent to put it first is still on its way.
>    Action: Ticket f275-01 (lead): a project started from the page goes first and every other project moves down one place.
> 2. **Only projects started from the page, not ones added in a terminal**: Your note is about the web form, and I'd keep it to that. `softfield init` in a terminal often brings in an old folder you aren't in a hurry for, so it still goes last. A forgotten project that comes back keeps its old place, as today. If you'd rather have every new project first, say so: it's the same ticket with one rule fewer.
>    Action: Decision D1 in the card doc. Tell me if terminal projects should go first too.
> 3. **An order sent while a new project waits could push it back to last**: This is a risk you didn't mention. Say you press Start it and then reorder the others before the runner's next pick. The order you send can't name the new project, because it isn't a project yet, and today anything an order leaves out goes to the end. With that, your new project would end up last again. So a project that is being set up and is missing from a sent order goes first, not last.
>    Action: Decision D2, in the same ticket f275-01.
> 4. **Its plate shows at the top as soon as you press Start it**: Today the dashed plate of a project on its way is drawn at the bottom of the list. It moves to the top, so the page matches where the project will go. The mock-up shows Today and Proposed on your six projects: the plate just after Start it, then the list after the runner's pick, with the new project at #1.
>    Action: Ticket f275-02 (developer), built from .softfield/cards/f275-mockup/new-project-first.html. It doesn't wait for f275-01, so the line never waits on the lead alone.
> 5. **Cost and where it runs**: Two small tickets of about 14 minutes each, with Claude's work being the lead ticket only. They run in F275's place on the board, which is last among the ready cards. Drag F275 up on the board if you want it sooner.
>    Action: Nothing, unless you move the card.
>
> Proposals:
> - F275: a project started from the Projects page goes first (plan)
> - Mock-up: a new project at the top of the Projects page (mockup)
