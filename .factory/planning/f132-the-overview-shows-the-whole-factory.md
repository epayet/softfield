# F132: One view of the whole factory: the top bar, the Overview, Jobs and the floor

The planning thread behind F132's plan, oldest first, as it was when the owner approved it.

## The lead, 2026-10-20 14:07

> Merged F160 here: the top bar on what's running atm is a bit buggy depending…

## The owner, 2026-10-20 14:07

> From F160, merged here:
> the top bar on what's running atm is a bit buggy depending on what project i'm looking at, it should the same regardless of current project viewed. similalrly, the overview should be the same across all projects, as there is one factory and runner for all projects. right now a developer ticket is working on softfield but top bar says Running: travel-companion · picking the next ticket.

## The lead, 2026-10-20 16:43

> I found why the top bar was wrong and drafted the plan to make the Overview cover the whole factory, with a mock-up and eight tickets. All eight pass the ticket checks.
>
> 1. **Why the top bar said travel-companion**: One runner serves every project, but each project keeps its own live run. The two projects waiting their turn say "picking the next ticket" the whole time another project's job runs. The top bar's ranking treats that line the same as a real job, and on a tie it picks the first project in your order, which is travel-companion. Travel-companion's 9 ready tickets all wait for m1-06-replan, which is waiting for Claude's 5-hour window, so it really had nothing to run. The bar was already the same on every page; it was just wrong on all of them. The f17 review spotted this and put it aside because only one runner ran back then. Since you set up several projects, three runs are live at once.
>    Action: f132-01, a small developer ticket: a running job always comes before a project that is only between jobs. I gave it priority 2 so it goes ahead of the rest of the card, because the bar is wrong on every page.
> 2. **The Overview, the same for every project**: Now, the queue, Next in line and Needs you show every project, each item with a small project label (only when there is more than one project). Next in line follows the runner's real order: every project's planning replies and reviews first, then tickets project by project in your order. A project that comes first but can't run anything gets one "Passed over" line saying why. Today that is travel-companion, held by the Claude window.
>    Action: f132-02, a lead ticket. It waits for f142-01 (F142, Phone notifications: every project), which changes the same code first and is planned at priority 3. f132-03 does the same for While you were away.
> 3. **Mock-up: the Overview today and proposed, on this afternoon's data**: Today is the live page as it looks with softfield picked. Proposed shows the same page whichever project is picked: the bar follows the job, each project's desk and notices are listed, the queue reads "63 tickets waiting: softfield 54 · travel-companion 9", and the project label is a new shape, plain with corner ticks and no status colour. On a wide screen the two versions sit side by side; on a phone there is a Today / Proposed switch.
>    Action: The UI tickets name the mock-up as the picture to build.
> 4. **Savings and the Claude chart: move them to each project's page?**: The Savings panel currently says "so far on F160-THE-TOP-BAR…", a card that was merged away this morning. It shows the newest card not yet done, and since every plant is now a card, that is just the newest plant. Adding these up across the whole factory doesn't mean much, because savings belong to a project's own work. My recommendation (A): move both panels to each project's page, as "Savings from delegating on <project>, so far" over all of that project's tickets. (B) Keep them on the Overview, added up across every project. (C) Remove them.
>    Action: f132-04 is written for A; your answer changes only that ticket.
> 5. **The project picker moves next to the pages it changes**: The card asked whether the picker stays in the top bar. My answer: it moves into the row of page tabs, right in front of Planning, Board and Tickets, and those three are drawn as one group. The tab order doesn't change. Every other tab is the whole factory's, and those pages' breadcrumbs start with "The whole factory".
>    Action: f132-08, a developer ticket.
> 6. **The factory floor, Jobs, Runs and Timeline cover every project too**: There is one set of machines, so there is one floor: the field counts every project's cards, and each crate shows which project it belongs to. Jobs and Runs get a Project column. The Timeline currently opens on that same merged-away card and draws nothing, so it will open on the last 24 hours of every project instead.
>    Action: f132-05 is a lead ticket, because it touches a lot of code shared by several pages. f132-06 and f132-07 are developer tickets.
> 7. **Overlap with the Projects page**: The Projects page already shows a short "Now" line and the Needs-you totals. Once the Overview covers every project, that is a small repeat, but it's harmless on the page where you order your projects. I'm leaving it as it is.
>    Action: Nothing.
> 8. **A merged card's record stays behind**: When a card is merged away, its milestone record stays in the database. F160 and three F107 records are still there, and that is why Savings and the Timeline landed on F160. This plan removes the code that picks "the newest card", so nothing visible depends on those records any more. Cleaning up the merge itself belongs to F49's merge work.
>    Action: To plant, if you want it fixed: "When a card is merged away, its milestone row goes from the database too (F160 and three F107 rows are left today)."
>
> Proposals:
> - F132: one view of the whole factory (plan)
> - F132 mock-up: the Overview today and proposed (mockup)
