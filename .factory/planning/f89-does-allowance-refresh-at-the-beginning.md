# F89: Claude's meters: a fresh reading before each job, and the time of the reading

The planning thread behind F89's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:29

> Or perhaps even when I refresh the page?

## The lead, 2026-10-27 04:02

> I answered both of your questions from the code and drafted a two-ticket plan, with a mock-up of the planning room's "The lead's window" tile. Nothing is queued until you approve it from the dashboard.
>
> 1. **At the end of a planner task: yes**: Each Claude job's own output carries the current numbers for Claude's 5-hour and week windows, and planner replies are Claude jobs. The runner saves those numbers when the job ends. That's why the meters move after each reply: the last reading was saved at 03:59 today, when a reply ended (5-hour window 18%, week 10%).
>    Action: Nothing.
> 2. **At the start of a planner task: no, it uses the last reading**: There is a quick check that reads the windows before work ($0.006, about 3 seconds). It only runs before lead tickets, checkpoints, escalations and directions, never before a planner reply. It also runs at most once per runner session, and a session lasts hours. So a planner reply usually starts with whatever the previous job read.
>    Action: Ticket f89-01: the check runs before any Claude job, planner replies included, every time the reading is over 10 minutes old, not just once per session. At most about six checks an hour, roughly $0.04.
> 3. **When you refresh the page: no, and I'd keep it that way**: Refreshing reads the database, so it shows the last saved reading. There's no free way to ask Claude for its usage: the only way is to run a small Claude job. Running one on every refresh would make the dashboard start Claude jobs on the runner's own login, every time you pull down on your phone. Today the dashboard only reads and never starts anything. One thing already works: once a window's reset time has passed, the meter says "reset since, no new reading" instead of showing an old percentage.
>    Action: No check on refresh. Instead, the runner checks before every job when the reading is old (point 2), and each meter says when it was read (point 4), so you can always tell how fresh the number is.
> 4. **Each meter says when it was read**: In the planning room, "The lead's window" gets "read at 03:59" on its header, said once because both windows come from the same reading. Each Claude row in the Overview's allowance gets the same words. A reading from another day shows the date: "read on Oct 26 22:10".
>    Action: Ticket f89-02 (developer), built from .factory/cards/f89-mockup/lead-window.html. It waits for the ticket of F32 (The 5-hour gauge says when it resets), which changes the same tile.
>
> Proposals:
> - F89: a fresh reading before every Claude job, and meters that say when they were read (plan)
