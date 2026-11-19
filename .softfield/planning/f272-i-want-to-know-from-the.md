# F272: The top bar says how long the job has run and which attempt it is

The planning thread behind F272's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-19 11:07

> I want to know from the headbar how long the job has been running and which attempt it is. if there is not much space, could be a hover mouse on desktop and part of the existing tooltip tap on mobile

## The lead, 2026-11-19 11:12

> I've drafted one developer ticket and a mock-up for showing the job's running time and attempt in the top bar. Ticket checks pass. Nothing is queued until you approve.
>
> 1. **Where it shows: a plate on a wide screen, hover when narrower, the tap on a phone**: On a desktop wider than 1200 px, a small "Job" plate sits right after the words. It looks like the "On" plate and reads e.g. "1 h 5 min · attempt 2 of 3". Under 1200 px the plate goes, so the ticket's name keeps its room, and hovering the words or the dot shows a second line: "Job running 1 h 5 min · attempt 2 of 3". On a phone, tapping the dot shows that same line above "Computer on …". Nothing new is added to the phone's row. I'm pushing back a little on hover-only for the desktop: you check how long a job has run often, and on a wide screen there's room to show it without hovering.
>    Action: Mock-up `.softfield/cards/f272-mockup/job-clock.html` (Today and Proposed, using travel-companion's job 2463 from this morning), and ticket f272-01.
> 2. **Plate or hover only on a wide screen?**: I recommend the plate from 1200 px, as drawn. Alternatives: (a) hover only, as you suggested: the bar stays as calm as today, but you need a mouse to see the time; (b) the plate at any desktop width: the ticket's name gets cut to "…" sooner (F256, The top bar on one line, shortens the words when the row is tight).
>    Action: If you choose (a) or (b), I'll change D3 and the ticket.
> 3. **The attempt only shows where it means a try**: The job's attempt number only means a try on a ticket. On a planner it just counts that role's jobs: right now the Overview's "Now" panel says "attempt 2" on the planner answering you, which is misleading. So the bar shows "attempt 2 of 3" for a developer, "attempt 3 of 3, the last" when the lead has given direction, and "attempt 2" on a lead ticket, which has no limit on tries. A planner, a review or a checkpoint shows the time alone. The same ticket fixes the "Now" panel to use the same words.
>    Action: D2 in F272's doc, in ticket f272-01.
> 4. **The time counts on by itself, in the "On" plate's words**: The time uses the same words as the computer's "On" plate ("14 min", "1 h 5 min") and moves forward with the bar's 5-second refresh, with no reload. There's nothing to show between jobs, while waiting for Claude, when idle or when stopped, so the plate isn't there then.
>    Action: D1, D3 and D4 in F272's doc.
> 5. **It comes after the top-bar cards**: f272-01 waits for F256 (The top bar on one line), which sets the row's heights and the "…". F256 itself waits for F194 (The menu: Overview, Planning, Board in fixed places), and F194 waits for F132 (One view of the whole factory). All of them change the same lines of the bar, so building F272 first would mean redoing it. It's one developer ticket of difficulty 3, about one ticket's work (16 minutes lately).
>    Action: depends_on f256-01-top-row-in-line.
>
> Proposals:
> - F272: the job's time and attempt in the top bar (plan)
> - F272 mock-up: the job's time and attempt in the top bar (mockup)
