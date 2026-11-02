# F138: Run again right after Ctrl-C, without the 2-minute refusal

The planning thread behind F138's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-29 18:56

> Plan this card.

## The lead, 2026-10-29 20:15

> I planned F138 with one lead ticket. The Ctrl-C wait is a bug: the runner already has the fix, but `softfield run` skips it.
>
> 1. **The fix you proposed exists already; `softfield run` skips it**: Since f2-03, every runner command ends the runs it left open when it exits, a Ctrl-C included (`runner/cli.py`, `main`, its last step). `runner run --here` goes through that step, so it never had this wait. `softfield run`, the command for every project, returns before it, so the step never runs. A Ctrl-C while the factory waits is fine, because that loop closes its own runs. A Ctrl-C during a job leaves the run looking live until its heartbeat is 2 minutes old. The metrics database has 16 runs since 2026-10-15 that never got an end.
>    Action: Ticket f138-01: `softfield run` ends its runs on exit the same way the other commands do. That is a few lines in cli.py plus a test, with no new mechanism.
> 2. **The cut-off job is still picked up at the next start**: The next start finds the interrupted job from state.json, not from the run's row. Ending the row on Ctrl-C changes nothing there: `--here` has worked this way since f2-03. The ticket checks it with a test.
>    Action: Covered by f138-01's acceptance criteria.
> 3. **The refusal says how long to wait**: With the fix, this message only shows when a run really might be live: a kill -9, a crash, or a second terminal. In those cases the 2-minute rule stays as a guard. I agree with your idea of saying the time left, and it costs little. The message becomes: "a run of softfield was live at 09:31:45 and may still be: one runner at a time; if you stopped it, try again in 28 s".
>    Action: In the same ticket, so there is no second one.
> 4. **No mock-up**: This only changes the terminal. No dashboard page shows anything different.
>    Action: Nothing.
>
> Proposals:
> - F138, Run again right after Ctrl-C (plan)
