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

## The lead, 2026-10-20 22:05

> Approved by the owner on 2026-10-20: approved plan/f132: queued f132-01-bar-follows-the-job, f132-02-overview-live-every-project, f132-03-away-every-project, f132-04-savings-on-project-page, f132-05-floor-every-project, f132-06-jobs-runs-every-project, f132-07-timeline-every-project, f132-08-picker-in-the-tabs

## The runner, 2026-10-21 15:56

> f132-01-bar-follows-the-job blocked: the finished work failed check-all; its work is on task/f132-01-bar-follows-the-job.
> Its work is on task/f132-01-bar-follows-the-job; its run's logs are in .factory/var/runs/20261021-090717/f132-01-bar-follows-the-job.
> What went wrong, and what is the fix? Propose it as a replan: the ticket reworked, split or set aside.

## The lead, 2026-10-21 15:59

> f132-01's code was right; it was blocked only because the full test run is now longer than the 20-minute limit check-all gives it. Below is the fix as a replan.
>
> 1. **What went wrong**: The code was fine once the escalation finished it. Every check passed except the full test run, which check-all stops after 1200 s (20 minutes). That run already took 1100–1170 s on 20 and 21 Oct. The ticket's twelve new page tests added about 40 s and pushed it over the limit, three times. f15-09 (F15, Reprioritising tickets) was cut the same way yesterday. The escalation raised the limit to 1800 s, but only on its own branch. The runner keeps a project's settings from when it starts that project, until the next day or a restart, so that raise could never have helped.
>    Action: f132-09, below.
> 2. **Fix 1: a 30-minute limit that takes effect straight away (f132-09)**: A lead ticket at priority 0, so it runs next. It raises the limit to 1800 s on main. It also makes the runner reload a project's settings at its next round whenever they change on main, so a change like this never waits for a restart again. Its own check-all still runs under the old 1200 s, and main's tests take about 1170 s today, so it adds no slow test. Every other ticket now runs within about 30 s of being cut, so this one has to go first.
>    Action: Approve the replan.
> 3. **Fix 2: f132-01 comes back as a lead ticket that copies the finished work**: It comes back as a lead ticket, because the finished branch also changes the developer's notes, a protected file. Back as a developer ticket, the check that guards protected files would fail it. The lead copies the change from the kept branch (the ranking fix, the backlog line, the note) and rewrites the tests so they call the ranking directly. Only one test goes through the pages. The cases stay the same, but they add under 10 s instead of 40. It waits for f132-09.
>    Action: Approve the replan.
> 4. **The test run keeps getting longer**: The full run went from 750 s on 13 Oct to about 1170 s now. The dashboard's app test file alone takes 345 s for 104 tests, more than 3 s each, because every test loads pages. Raising the limit buys time but doesn't stop the growth.
>    Action: To plant, if you want it handled: "The full test suite takes 19 minutes and grows each day: find the slowest tests (tests/factory_dashboard/test_app.py takes 3 s a test) and make them faster, without new dependencies unless you agree."
> 5. **Pause first?**: No need. Nothing in the queue touches f132-01 or f132-09 before your Approve, and approving puts f132-09 next.
>    Action: Nothing.
>
> Proposals:
> - F132: raise the test time limit, then land f132-01 from its branch (replan)

## The lead, 2026-10-22 07:55

> Done in a terminal session tonight, so this replan isn't applied (its branch is kept as superseded/plan-f132-2026-10-21). f132-01's finished work was landed from its branch: it had been cut only by the 20-minute test limit, and check-all now passes in 5 minutes on 16 workers (F71). No limit was raised, so f132-09 is dropped.

## The lead, 2026-10-22 08:42

> Rejected by the owner on 2026-10-22: won't do

## The lead, 2026-10-27 04:03

> Merged F92 here: The owner said that Claude per milestone on the Overview isn't very useful, especially on a phone, and asked why the savings panel was stuck on M4. Answered: the panel follows the newest card not done yet, and F132's D8 (ticket f132-04) moves both panels to the project's page. Still open: whether the Claude-per-milestone chart needs a phone-friendly form once it is on the project page.

## The owner, 2026-10-27 04:03

> From F92, merged here:
> Claude per milestone on overview is not super useful especially on mobile.
> Savings from delegating so far on M4, why is this stuck on M4?

## The lead, 2026-10-27 14:02

> I've changed one ticket, f132-04: the Claude per milestone chart is now removed, not moved. Your savings question is answered below.
>
> 1. **Why savings looked stuck on M4**: The savings panel doesn't follow a fixed card. It shows whichever card is newest and not done yet. On coucou's Overview that is M4, Sender app, so it stays on M4. On softfield's it changes with every new plant: F160 on 20 Oct, F177 today. That is why it looks either frozen or random.
>    Action: f132-04 moves savings to each project's page, where it counts all of that project's delegated tickets instead of one card's. It's already queued and waits for f132-02.
> 2. **Claude per milestone: removed, not moved**: I agree it isn't worth keeping. Moving it to the project page would only move a chart nobody reads. The Milestones page already has charts for Claude's dollars per merged ticket and net savings per milestone, so this one adds nothing. The savings panel itself is three large numbers, which read fine on a phone, so that one moves as it is.
>    Action: Approve the replan: f132-04 deletes the chart and its code. The mock-up's grey panel now says this.
> 3. **No pause needed**: f132-04 can't start until f132-02 has merged, so changing it now can't collide with a running job.
>    Action: Nothing.
>
> Proposals:
> - F132: savings moves to the project page, the Claude per milestone chart goes (replan)
