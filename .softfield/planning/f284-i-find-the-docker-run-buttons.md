# F284: Run and Stop show what the app is doing, with its logs on its plate

The planning thread behind F284's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-21 05:04

> I find the docker run buttons a bit unresponsive. If I click run it says starting and if I refresh the page it's gone and I have to click run again. I find it difficult to know if it's doing things. The logs get me to a different page rather than show there directly. There's been a few times where I thought it was doing nothing but it was actually doing something. I had to click pause resume a few times  on the log page and eventually it works

## The lead, 2026-11-23 22:30

> I've planned F284 as three tickets plus a mock-up (`.softfield/cards/f284-mockup/app-row.html`). The cause of every symptom you describe is in the code, not in your clicks.
>
> 1. **Why Run seems to do nothing**: Pressing Run makes one request that waits for the whole `docker compose up --build`, and that can take minutes. 'starting…' only means your browser is waiting for that answer; the server keeps no record of it. While the image builds there are no containers yet, so after a refresh the row asks Docker, gets told Stopped, and shows Run again. A second Run waits up to 60 s and then says 'busy' or starts another build. The dashboard also reloads after every Softfield merge, about every 46 minutes lately. A press caught by a reload loses its answer and stays on 'starting…' for good.
>    Action: Tickets f284-01 and f284-02 (points 3 and 4).
> 2. **Pause and Resume on the logs page weren't the fix**: Those buttons only stop and restart the page's 5-second refresh; they can't start anything. The page shows the app's own output, which is empty until the containers start. The build's output is thrown away, so while the app built, the page showed nothing. The lines appeared when the build finished, which happened to come after your presses.
>    Action: Ticket f284-03 shows the build's lines on the logs page and in the plate (point 5).
> 3. **Run and Stop answer at once, and the app's state is saved**: Run and Stop start the Docker command in its own process and answer right away. A dashboard reload doesn't end that process. While the command runs, it writes what it is doing (starting, stopping or updating), since when, and the build output to a file beside the app. The row reads that file, so a refresh, a reload or another device all show 'Starting'. A second press while the app is busy changes nothing. The runner's own rebuild after a merge shows as 'Updating'. All Docker calls stay in `runner/stacks.py` and the dashboard's guard stays, so this is a lead ticket.
>    Action: f284-01 (lead): runner/stacks.py and the Run and Stop routes, test first.
> 4. **A busy row shows that it's working and refreshes itself**: While busy, the row has a pulsing hazard light and a dashed hazard edge, like other things that are on their way. It shows what is happening and for how long ('Building the image · 1 min 40 s'), plus the build's last line. It has no Run or Stop button, so you can't press twice by mistake. It refreshes every 5 s and stops once the app has settled (Running, Stopped or Crashed). In the mock-up, see the duck-ascii-test and travel-companion rows.
>    Action: f284-02 (developer), built from the mock-up.
> 5. **Logs open on the project's plate**: Logs becomes a toggle. It opens a box under the row with the last 40 lines, 12 lines tall, refreshed every 5 s while open. While the app builds, the box shows the build first, then the app's lines, or 'No lines yet: the app hasn't started.' I'd keep the logs page and link it from the box as 'All lines →'. A full log inside a plate would push the other projects off a phone screen.
>    Action: f284-03 (developer), built from the mock-up's open box and logs page.
> 6. **Should rows refresh when nothing is happening?**: I'd refresh a row only while it is busy. Then the page doesn't ask Docker about every project every 5 s just to show the same 'Running'. The cost: if an app crashes while you have the page open, you only see it after a reload. The overview's Needs you list still shows a crash. Alternative: every settled row also refreshes once a minute.
>    Action: As planned unless you choose the once-a-minute refresh; then f284-02 adds it.
> 7. **When it runs**: Three tickets, about 2½ hours of runner time. It touches none of the waiting tickets, so no pause is needed. It joins the board where the runner puts new cards. If it bothers you every day, drag it up: it doesn't conflict with the Projects-page cards ahead of it (F123, Projects page drag to reorder; F124, Pause one project; F262, Archive a project), which change the plate around the row, not the row.
>    Action: Nothing, unless you move it on the board.
>
> Proposals:
> - F284: Run and Stop show what the app is doing, with its logs on its plate (plan)
> - F284 mock-up: an app row that shows what it is doing (mockup)
