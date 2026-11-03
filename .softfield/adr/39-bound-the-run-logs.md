# ADR 39: Bound the run logs under `.softfield/var/runs/`

- **Status:** Proposed
- **Date:** 2026-10-30
- **Deciders:** project owner (accepts), Claude (drafts)
- **Evidence:** F175 (owner, 2026-10-26: the disk fills while the factory runs). `softfield look disk` on 2026-10-30: `.softfield/var/runs/` holds 773 MB in 3,096 files, every job's log since the first run, and it only grows (+0.7 MB between f175-01 and f175-03). It is the one place the factory fills that nothing bounds; `/tmp` is fixed by f175-02 and the empty git template in tests.

## Context
- The logs are the owner's record of what each job did; the dashboard's job pages read them, and the metrics database points at them. Deleting any changes what the owner can look back at, so f175-03 did not touch them.
- At the current rate (a few hundred MB a month) it is not urgent, but it is unbounded.

## Decisions (open, for the owner)
1. **Keep every log for N days (suggested 90), then compress it** (`.log` → `.log.gz`, same name plus `.gz`; the job page reads either). Nothing is deleted.
2. **Or delete after a longer time (suggested 365 days),** only logs of jobs whose ticket is merged and whose milestone is signed off.
3. **Back up first, if anything is deleted:** the daily Dropbox backup holds the metrics database only (`runner/backup.py`), not these logs, so item 2 needs the backup to take them first. Item 1 deletes nothing and needs none.

**The lead's recommendation (F175's review, 2026-11-03):** item 1 alone, as one lead ticket, with item 2 turned down. Logs are text and compress well, the owner keeps every one, and it adds no backup work. `.softfield/var/runs/` took about 800 MB on the disk on 2026-11-03, growing by a few MB a day, so this is not urgent. (The 773 MB above is the files' length, read before `look disk` changed, so the two don't subtract exactly.)

## Alternatives turned down
- **Leave it:** 773 MB is small on today's disk; the cost is a slow, silent growth.
- **Delete on a size cap:** the oldest logs go first, whichever milestone is still open.

## What doesn't change
The metrics database, planning threads, requests and ratings; the runner's `/tmp` folders (ADR-less, f175-02).
