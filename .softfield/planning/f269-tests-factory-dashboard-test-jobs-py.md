# F269: The 200-jobs test writes its jobs in one transaction

The planning thread behind F269's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-18 19:13

> tests/factory_dashboard/test_jobs.py's test_more_than_200_jobs_shows_200_and_count spends 13 s in setup writing 200 jobs one at a time: write them in one transaction so it takes under a second. From F71's review.

## The lead, 2026-11-18 19:14

> I've drafted one small developer ticket for this card and it passes the ticket check. Nothing is queued until you approve.
>
> 1. **Why it takes 13 s**: The test's setup writes 205 jobs. Each one is three database writes (its ticket, its start, its finish), so 615 in all. The test database saves after every write and waits for the disk each time. Doing all 615 as one save should bring the setup under a second. Nothing in the runner or the dashboard changes, only the test's setup code.
>    Action: One developer ticket: the setup wraps all its writes in a single save, the same way the runner already saves the board's order.
> 2. **How we'll know it worked**: I'm not adding a test that fails when the setup is slow: on a busy machine that kind of test fails for no reason. Instead, the developer runs the jobs tests with their timings shown, checks the setup is under 1 s, and puts the before and after times in the commit message. The test itself stays exactly as it is.
>    Action: This is in the ticket's Done when.
> 3. **The other slow test F71's review named**: F71's review (finding F3) also named the tests in tests/factory_dashboard/test_shots.py, at about 12.5 s, because they wait out real timeouts. That's a different fix with a different cause, so I've kept this card to the jobs test.
>    Action: If you want that one fixed too, plant it as its own card: “tests/factory_dashboard/test_shots.py spends 12.5 s waiting out real timeouts: make them use a fake clock or short limits. From F71's review (F3).”
>
> Proposals:
> - F269, the 200-jobs test writes its jobs in one transaction (plan)
