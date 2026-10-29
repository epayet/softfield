# F187: Store every time in UTC, show local time on screen only

The planning thread behind F187's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-29 08:14

> Store every time in UTC. The runner writes local time (+01:00 before 25 Oct) and the dashboard writes UTC, so times sort wrong as text. Write UTC everywhere, show local time on screen only, and convert the old rows once after the daily backup.

## The lead, 2026-10-29 08:19

> I've drafted the plan for F187 on its branch: three tickets, with the facts taken from the code and the database.
>
> 1. **Agreed, and the data shows why**: The machine's clock is on UK time. The runner wrote +01:00 until 25 Oct and +00:00 since, while the dashboard always writes UTC. That leaves about 4,200 rows at +01:00 (1,514 usage events, 1,377 jobs, 516 planner messages, 458 runs, 192 desk items, 154 requests). Your requests are mixed even within one day: 666 from the dashboard and 154 from the runner before 25 Oct. About 30 queries order or compare times as text. F86 (Tracking the time the owner spent) already had to work around this.
>    Action: The plan below.
> 2. **Why it matters even though it looks fine now**: UK winter time is the same as UTC, so new rows are already +00:00 and nothing looks wrong until 28 Mar 2027. That also means a missed conversion to local time would stay hidden all winter. So the tests run in Paris time, where local and UTC differ, and a mistake shows straight away.
>    Action: Decision D6 in the plan.
> 3. **Fix the clocks, not every place that writes a time**: There are about 60 places that write a time, but they all take it from four clocks in the runner. Making those four return UTC is smaller and harder to get wrong than making the database rewrite every time it is given. The dashboard's clock is already UTC. Times you read (the console, reports, desk wording, the pages) are converted to local time just before they are shown.
>    Action: Ticket 01 (lead) and ticket 02 (developer).
> 4. **Names and dates stay in local time**: Run folder names, backup file names and the dates in card docs ('Planted by the owner on 2026-10-29') stay local. You read them as names, and the backfill reads old run folders as local time. Renaming them would gain nothing.
>    Action: Decision D4.
> 5. **The conversion only runs right after a backup copy**: It is a one-off step, built the same way as F55's: it runs right after a Dropbox copy is written, so that copy still holds the old rows. On a machine with no backup set up, it first writes its own copy next to the database. The conversion is all or nothing: if it ever hit a clash it would undo itself, delete nothing and say so once on the console. Each time keeps the same moment and only changes how it is written, including the repeated hour of 25 Oct, because every stored value has its offset.
>    Action: Ticket 03 (lead, tests written first because it rewrites your data). It waits for 01 and 02, so no clock or page is still on local time when the rows change.
> 6. **No mock-up**: Nothing on screen changes: every page shows the same local clock times as today, in winter and in summer. Part of the point is that it must look the same.
>    Action: None.
> 7. **When it runs**: Once approved, the card goes to the bottom of Ready, behind 84 tickets. It is three tickets, about an hour. Drag it up the board if you want the mixed times fixed before more rows pile up; every week adds a few hundred.
>    Action: Your call on the board.
>
> Proposals:
> - F187: store every time in UTC, show local time (plan)
