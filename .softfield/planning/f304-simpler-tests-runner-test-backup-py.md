# F304: Backup tests use the shared fake clock and THURSDAY

The planning thread behind F304's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-25 20:56

> Simpler: tests/runner/test_backup.py keeps its own `fake_clock` fixture and `THURSDAY` constant, which repeat the ones now in tests/runner/conftest.py; drop them for the shared ones (about 12 lines). From F290's review.

## The lead, 2026-11-25 21:35

> I've drafted one small ticket for a developer, and it passes the ticket check. It's a cleanup of the backup tests only, so there's nothing to draw.
>
> 1. **Agreed: the copies are redundant**: I read both files. `tests/runner/test_backup.py` defines the same `THURSDAY` date and its own `fake_clock` fixture, which is shorter than the shared one in `tests/runner/conftest.py`. The only thing the shared fixture adds is that `subprocess` keeps its real sleep, and the backup tests don't depend on that. Switching to the shared ones changes no test.
>    Action: One developer ticket, tests only (f304-01). It deletes the two copies, imports `THURSDAY` from the shared file, and keeps every test's name and body.
> 2. **Another ticket edits the same file**: F178, Show the backups on the dashboard, has a lead ticket waiting (f178-01) that also edits `tests/runner/test_backup.py`. The two changes are in different parts of the file, so whichever runs second merges cleanly or has a conflict of a line or two. Neither ticket has to wait for the other.
>    Action: Nothing.
>
> Proposals:
> - F304: backup tests use the shared fake clock (plan)
