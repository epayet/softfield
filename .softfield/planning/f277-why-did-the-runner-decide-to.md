# F277: A project's setup goes before every other job the runner could pick

The planning thread behind F277's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-19 16:12

> why did the runner decide to pick a planner task rather than a setup task. setup is more important

## The lead, 2026-11-19 16:16

> I found the cause in the metrics and drafted one lead ticket to make setups go first. I couldn't open duck-ascii-test's run log, so the second reply's cause isn't proven yet.
>
> 1. **Why F275's reply went before the duck-ascii-test setup**: At 16:04:54 one batch of your requests started duck-ascii-test and queued my reply on F275. Softfield's turn applied that batch. The runner only reads the list of projects at the start of a round, so duck-ascii-test wasn't in this round yet. Softfield's turn then ran its own queued job, F275's reply (16:05 to 16:07). waifu-gallery's setup waited the same way this morning, behind F122's reply.
>    Action: Ticket f277-01: a turn that starts a project ends at once, so the next round reads the projects again and runs the setup first.
> 2. **F276's reply also went before the setup, which shouldn't have happened**: duck-ascii-test's session opened at 16:07:52, first in your projects' order (priority 1, Softfield is 5). Its setup should then have gone before Softfield's planner replies. F276's reply still ran first (16:08 to 16:10), and the setup only started at 16:10:37. I couldn't open duck-ascii-test's run log from here, so I don't know why yet.
>    Action: The same ticket finds the cause from that log, or rebuilds that round in a test first, and fixes it. The test must fail without the fix.
> 3. **Setup ahead of the fast lane too?**: I agree setup is more important, and I'd put it ahead of the fast lane as well. A setup takes about 2 minutes, you're waiting on the Projects page for it, and a fast-lane ticket can take 15 minutes or more. The other choice: setup right after the fast lane but before every planner reply, direction and ticket.
>    Action: D1 says before the fast lane. Tell me if you'd rather it went after it.
> 4. **Where it goes on the board**: It's one ticket for me (the runner's code is protected) and nothing changes on screen, so no mock-up. After you approve, it joins the board where you drop the card. Until it's built, a new project can wait about one planner reply behind Softfield's.
>    Action: Drag F277 up the board if you want it done soon.
>
> Proposals:
> - F277: a project's setup goes first (plan)
