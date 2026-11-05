# Review: F187, every time stored in UTC, shown in local time

- **Status:** done, signed off by the owner on 2026-11-05.

## Sign-off sheet

### 1. What changed
- **Nothing should look different.** Every page, console line and report shows the same clock times as before. This winter the machine's time equals UTC anyway; the change matters from 28 March.
- **The factory now writes every new time in UTC,** so ordering times as text is ordering them in time, in summer too. Folder names, backup names and the dates written into cards stay in local time.
- **The old rows convert once, after the next daily backup.** The last copy is 2026-11-03 22:14, so the next one is due from 22:14 tonight, as soon as the runner next checks. The console will say "converted N stored times to UTC (F187)". **It hasn't happened yet:** 1,377 jobs, 458 runs, 1,514 usage events, 516 planner messages, 191 desk items and 154 requests still don't end in `+00:00`, and all of today's checks on it are from tests.
- **I checked your real data for clashes:** no two usage events or rating changes become the same time once converted, so the conversion shouldn't roll back.

### 2. How to test it yourself
Do these after the console has said "converted N stored times to UTC (F187)", tonight or tomorrow:
1. Open the Overview, the line, the desk and a planning thread on your phone. An old thread message should show the same clock time as before: a message from early October still reads at its summer time.
2. Open the Timeline, Runs and Jobs pages. An old job from before 25 October should read with its summer time and `+01:00`, and a new one with `+00:00`.
3. Open the Dropbox folder `software-factory-backups`. The copy taken just before the conversion is the one to keep safe: it still holds the old rows as they were.

The lead can confirm the counts: all of them should reach 0 once the conversion has run.

### 3. Left for later
- With no backup set, a conversion that keeps failing writes a copy beside the database each time it retries. This machine has a backup set, so it doesn't apply here.
- The runner's old JSON state lapses within a day, as the card planned. The product (`coucou/`) isn't part of this card.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-29: planned from your note.
- 2026-11-02 22:10 ([session](../sessions/2026-11-02-2210.md)): `f187-02-pages-show-local-time`, three failed attempts by the local model (34 minutes), then the lead finished it on its branch in 17 minutes.
- 2026-11-04 06:27 ([session](../sessions/2026-11-04-0627.md)): `f187-01-runner-clocks-utc`, the lead's ticket on Sonnet, first attempt, 19 minutes.
- 2026-11-04 06:50 ([session](../sessions/2026-11-04-0650.md)): `f187-03-old-times-to-utc`, the lead's ticket on Sonnet, first attempt, 16 minutes.
- 2026-11-04 07:10: review round 1 fixed five findings itself.
- 2026-11-04 10:12: review round 2 had no fix merges to read. It confirmed round 1's fixes are unchanged and ran all of the runner's tests.
- Lessons:
  - **UK winter hides this whole class of bug.** Both reset-time bugs (F1, F2) pass on this machine today and would have appeared on 28 March. Only a test with the zone set to Paris can show them, and the card already asked for that.
  - **Changing what a clock returns changes every reader, not just the writers.** The card listed who writes through the clocks. `usage_limit_reset` reads `now` to mean "the machine's clock", and nothing marked it. The review found it by searching for every use of `now`'s zone.
  - **A sweep by column name misses renamed values.** The Timeline's `bar.start` holds a stored time under another name (F3). The review found it by searching templates for any field that could hold a time.
  - **The local model's ticket was too short.** The session's escalation note covers it, and `.softfield/developer.md` now has the worked example.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** run the factory's whole test suite once in a zone west of UTC as well as UTC and Paris. A slip that goes the other way, like resuming too early after a limit, shows best there. I'd plant it as a small card if the review's Paris tests ever miss something.
- **Factory:** make the suite fit a review's 10-minute limit for one command. The dashboard's tests alone took 16 minutes here. I'd start by running them in parallel, and plant that as a card of its own.

### 7. What clogged the factory line
- **The ticket that had to go first ran last.** 02 ran on 2 November, then 01 waited 30 hours 35 minutes (23:52 on 2 November to 06:27 on 4 November). Nothing was broken: other cards ahead on the board and their reviews took those hours. Nothing to unclog; the order inside the card held, since 03 waited for both.
- **The local model's three attempts on 02 took 34 minutes and merged nothing,** then 29 minutes' wait before the escalation started. Fix already made: the worked example in `.softfield/developer.md`. A ticket whose output depends on the machine's zone should be run against the suite when it's planned.
- **The test suite's length:** the full run didn't fit this review's limits and was stopped at about 88%, then the dashboard's 1,163 tests took another 16 minutes in three batches. To unclog it, see the parallel run in "What next".

## What was built
- **`f187-01-runner-clocks-utc`:** `loop.now()`, `owner._now`, `cli.py`'s first thread and `backfill.py`'s times return UTC. `loop.local_clock()` gives the console its stamps. Every place the runner prints a time or writes a date for a person now converts first.
- **`f187-02-pages-show-local-time`:** `queries.local` and a `local` template filter, used on every page that prints a stored time. Dashboard tests now run in UTC, with `paris` and `london` fixtures.
- **`f187-03-old-times-to-utc`:** the `f187 utc` once step in `metrics.py`, run from `check_backup` right after a copy is written, or after a copy beside the database when no backup is set. One transaction; a clash rolls back and says so once.
- **Added by this review:** `usage_limit_reset` returns UTC and reads a bare clock on the machine's clock. The Timeline's table prints local time. A bench's folder is named in local time. Six new tests in another zone, and the `paris` fixture moved to `tests/runner/conftest.py`.

**Existing tests edited:**
- `test_line.py`: `night_db` now takes the `london` fixture, because its "overnight" is worked out from local 20:00. Fair.
- `test_milestones.py`: `test_how_it_grew_dates_planted_and_harvested…` now takes `paris`, because its fixture's times read 12:00 in that zone. Fair.
- In this review: only the `paris` fixture moved and an unused import went.

No French changed.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | A limit's reset was stored with its own offset, `+01:00` from 28 March | Fixed in `usage_limit_reset`, with a test |
| F2 | should-fix | claude | A bare "resets 5pm" was read as 5pm UTC | Fixed in `_zone`, with a test |
| F3 | should-fix | claude | The Timeline's jobs table printed stored times as they are | Fixed with the `local` filter, with a test |
| F4 | nit | claude | A bench's folder was named in UTC, against D4 | Fixed in one line |
| F5 | should-fix | claude | Most converted runner code had no test in another zone, against D6 | Four tests added for the riskiest; the plain conversions left, each read in this review |
| F6 | nit | report | A conversion that keeps failing logs at each check and, with no backup set, writes a copy each time | Not fixed: needs a rare failure on a machine with no backup, for a step that runs once |
| F7 | nit | report | Unused `now` parameters on two `_when`s, and a redundant `.astimezone(UTC)` in `_convert_old_times` | Not fixed: harmless |

**Round 2:** there were no fix merges, because round 1 made its fixes directly. F1 to F5 stay resolved: the files they changed are the same as at the end of round 1, and their tests pass. F6 and F7 stay as reported. No new findings.

What held up when I looked for trouble:
- The conversion's column list matches the schema; `merges_unread` is a list of card keys, not a time.
- A new database starts with the step done, and the real database still owes it.
- SQL text comparisons no longer meet a local offset: the dashboard's local times are parsed, never passed into SQL.
- The line's replay keeps using a local `since`, and `factory.js` slices its own server-sent clock, which is local.

Checkpoints: none read these tickets, so there's nothing to judge and no "missed".

**Done when, as of now:**
- The counts at 0, the console line and the Dropbox copy can only be checked after tonight's backup. The code paths are tested, on a copy and on a clash. At 10:12 today the step was still owed, as expected: 458 runs and 1,377 jobs still held old times, the same as round 1, and new rows were being written in UTC.
- "The same clock times as before" and "08:00+00:00 shows as 09:00" are tested in the zones given; the first needs your look on real pages.

## What was set aside
F6 and F7, as above. No bug tickets: neither is worth a run.

## Workflow observations
- Sonnet passed both lead tickets on the first attempt. Its misses (F1, F2, F4, F5) were all outside the ticket's list of clocks and display sites. Searching for the readers of a changed value is what caught them, so this is the review doing its job, and no change is needed.
- All five fixes were in protected code or a few lines, so I made them here rather than writing developer tickets.
- **How the fixes were checked:** ruff and mypy pass, and the dashboard's 1,163 tests pass, run in three batches. `tests/runner` has no complete final count: it ran first in a full run that showed no failure before the time limit stopped it at about 88%. The runner's tests were all in the part that finished, judging by the suite's size, and the new ones in `tests/runner` also passed on their own. The `E`s printed after that stop came from the stop itself: those tests passed when rerun.
- **Round 2 closes that gap for the runner:** all of `tests/runner` passes on current main, 1,882 tests in 6 minutes 27 seconds, as do the Timeline's 16. The dashboard's other tests weren't rerun in round 2: nothing of this card changed since their 1,163 passed in round 1.
- `softfield report` isn't among the commands a review may run, so the numbers below come from the runner.
- The ADR 02 entry is added. `runner/instructions/lead.md` still says to update "Known range" above, but `lead.md` has no such section; the line should lose that clause the next time the file is edited. Not worth a run.

<!-- runner report -->
<!-- /runner report -->
