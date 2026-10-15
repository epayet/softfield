# Review: F109, merged cards link to each other, both ways

- **Status:** reviewed, round 1; waiting for the owner's sign-off.

## Sign-off sheet

**Expected:** your note was "When plans get merged, I need to be able to go from one to the other (I have no links ATM)". A card merged away and the card that took its notes link to each other on their thread pages, both ways, for every merge already done too. A card's number is never given to a new card after a merge.
**Done when:** `/planning/f105` says "Merged into F51, <F51's title>" as a link; F51's page lists "Merged here" with F16 and F105, each with its title and date; the lead's line "/planning/f51" is a link; a new plant after a merge takes a new number.

### 1. What changed
- **On a merged card's page**, under its title: "Merged into F95, <F95's title> · 2026-10-13", a link straight to the card that holds its notes now. If a card was merged into one that was later merged too, the link goes to the last one.
- **On the kept card's page**, one "Merged here: F107, <F107's title> · date" line per card merged into it.
- **In place of the box to write in**, a merged card's page says "Merged into F95, …: the conversation and its plans are there", then links to F95's open plans and, once F95 is planned, "Planned: N tickets, M done".
- **A number used twice before** (F64, F73, F107) lists every card it went into, and keeps its box to write in, since a message there can't tell which card it is for. F73, which has a card again, says "An earlier F73 was merged into F43, …".
- **The lead's line** "The conversation goes on on F95's thread: /planning/f95" now shows that path as a link.
- **A new plant never reuses a number** that a conversation already has (f109-02, done with you on 2026-10-13).
- **Fixed in this review:** without it, every merged card would have said "An earlier F107 was merged…", and "Merged into F95" would have shown F107's note in place of F95's title.

### 2. How to test it yourself
1. On your phone, open the planning room, then `/planning/f105`: under the title it says "Merged into F51, …" with F51's own title. Tap it.
2. On F51's page: "Merged here" shows F16 and F105, each with its date. Tap F105 to go back.
3. Open `/planning/f107`: it lists two cards, F73 and F95, each with a block of its own, and the box to write in is still there.
4. Open `/planning/f24`: it links straight to F51 (F24 went into F16, then F16 into F51).
5. Open `/planning/f73`: "An earlier F73 was merged into F43, …", and the card's own title above it.
6. Plant two notes that say the same thing and let the lead merge them. Plant a third: it gets a new number. The merged one's page points to the kept one.

### 3. Left for later
- **The same links on the card's own page,** once F5's card page (f5-17) is on main: in the card's "Later" section.
- Nothing new in the backlog.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-13: planned with you. You did f109-02 (no number reused) in the terminal session.
- 2026-10-15 09:50 ([session](../sessions/2026-10-15-0950.md)): f109-01 and f109-03 merged, each on its third attempt, after a direction from the lead. 20.8M local tokens. The checkpoint found four flaws and wrote f109-04.
- 2026-10-15 15:32 ([session](../sessions/2026-10-15-1532.md)): f109-04 escalated after three attempts and was finished by the lead. 147k local tokens.
- 2026-10-15: this review, round 1. Four findings, all fixed in the review.
- Lessons:
  - **Test fixtures that don't look like real data hide real bugs.** The developer's tests left a merged card's doc on main and no milestone row behind it. A real merge does the opposite on both counts, which is exactly where the two worst bugs were. Reading the 19 real merge headings in `.factory/cards/` took a minute and showed both bugs.
  - **Fix tickets that touch `test_planning.py` (3,500 lines) are the lead's.** f109-04's first attempt did most of the work. The next two attempts re-read the file for ten minutes each and stopped with no edit, the second despite a direction. Now in `docs/task-writing.md`.
  - **A shell timeout used to leave tests running for hours** (three `pytest` processes at 95% CPU). The runner now ties every command to the process that started it (`runner/procs.py`), and the developer notes tell agents not to shorten `check-all`'s timeout.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - When a ticket's tests build data by hand, its ticket should name the real record to copy (here: "a merge removes the card's doc and keeps its row, marked removed"). This is a line for `docs/task-writing.md`, added below.
  - The checkpoint caught four real flaws but missed the two that mattered most. Both were visible only by checking the fixtures against real data. The checkpoint's brief could add "compare one fixture with a real record on main". It isn't worth a ticket until it misses something again.
  - F64, F73 and F107 still mix several conversations in one thread. As D5 decided, splitting them isn't worth a migration. They now say so.

### 7. What clogged the factory line
- **About 3 hours 20 minutes of developer time on f109-01 and f109-03** (6,199 s and 7,002 s), mostly attempts that stopped after "no edit for 10 min" (three times). Fix: planning-page tickets with UI and tests in `test_planning.py` go to the lead or get split smaller (the F14 rule, which f109-01 and f109-03 were close to).
- **About 44 minutes on f109-04**, two dead attempts before the escalation. Fix: the F109 lesson above (such fix tickets go to the lead).
- **A runner restart** after the lead changed `runner/`. Fix: none needed, by design.
- I couldn't read hours per wait from the metrics database here (a review job has no query command); the figures are from the session reports and the tickets' runner blocks.

## What was built
- **f109-01** (`factory_dashboard/planning.py`, `thread.html`): `_merge_links` reads the `### From F107: … (merged by … on …)` headings of every card on main, three to six `#` deep, so chains work. It returns the links into and from the thread, plus the merged card's last title for its heading. Lead lines without points have `/planning/<key>` turned into links, after escaping.
- **f109-03**: `_merged_on`, the block that replaces the box to write in on a merged card's page: the kept card, its open plans and its ticket count. With two kept cards the box stays.
- **f109-02**: done with the owner on 2026-10-13 (`eda0843`), outside this run.
- **f109-04** (checkpoint fix, finished by the lead): N and M counted over the same rows, a narrower `suppress`, the block's link text, and sharper tests.
- **Also on main in this range:** two runner fixes by the lead, not part of F109. Every command now runs under a watcher that kills its group when the runner dies (`runner/procs.py`, `PR_SET_PDEATHSIG` on Linux, with tests). The git author variables are cleared from the tests' environment (`runner/checks.py`). I read both and found them sound. The watcher only waits on SIGTERM, so the command keeps its grace period, and a command killed by a signal still reports it.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | blocking | claude | The header chose "An earlier F107 was merged…" whenever the key had a milestones row. A merge keeps the merged card's row, marked removed, so every one of the 19 merged cards would have said it | Fixed: the wording depends on the card being on main (`thread in known`), as in D4 and `_merged_on`. New test with a removed row |
| F2 | should-fix | claude | "Merged into F95, <title>" gave the merged card's own title (from the heading), so /planning/f107 would read "Merged into F95, overview page says I have this…" | Fixed: the kept card's title, read from its doc. "Merged here" keeps the heading's title, which is right there |
| F3 | should-fix | claude | Test fixtures unlike real merges: the merged doc left on main, headers no real card has (`# Milestone f95-plans-get-merged:`), odd filenames, a class name counted instead of the links read | Fixed in `tests/factory_dashboard/test_planning.py` |
| F4 | nit | claude | Links in the lead's lines dropped `?project=`, so they opened the default project's thread | Fixed: `_text_with_links` keeps the page's query |

Checkpoint findings (C935, after f109-01 and f109-03): all four confirmed, all fixed by f109-04. F1 and F2 were in the diffs that checkpoint read: marked missed.

Read and found sound:
- **Escaping:** the lead's text is escaped (`& < > "`) before links are added, and the link's key matches only `[a-z0-9-]`, so `| safe` lets nothing through. The owner's messages stay plain text (tested). Titles from card headings go through Jinja's autoescape.
- **Chains:** `card_notes` moves headings down one level, and the reader takes three to six `#`. On main, F24's `#####` heading in F51 links F24 straight to F51.
- **The count query** matches `F95-%`, so it can't pick up F950 (the dash), and it leaves out `later` and `removed` tickets.
- French: nothing to check, the dashboard is English only and no `coucou/locale/` file changed. Screenshots: no browser in this job.

Edited existing tests: f109-01 and f109-03 edited only the tests they added at the end of `test_planning.py` (the session reports flag the file). No test from before F109 was changed. This review rewrote fixtures in eight F109 tests and added one (see F1–F3).

Checks after the fixes: `uv run pytest -q tests/runner tests/factory_dashboard` gave 2,280 passed (15 min 56), ruff and mypy are clean on the edited files. The `tests/unit` and `tests/integration` folders named in the brief don't exist in this repo.

Score: 6/10. The design (read the headings, store nothing) is right, and it covers every past merge. But the headline line of Done when would have been wrong on every real card, twice over, while 25 tests passed, because the fixtures didn't look like a real merge.

Stop reason: none. Every finding is fixed; nothing is left for round 2.

## Factory
- **The flow:** three developer tickets. Two merged on their third attempt, one escalated and finished by the lead. One checkpoint, with four findings, all real. No stop for the owner, no park.
- **Models:** the local Qwen 3.6 35B spent 20.9M tokens. Five of its attempts ended "no edit after 10 min", all in planning-page work on the 3,500-line test file. Claude (Opus) gave directions, ran the checkpoint and the escalation, and did this review. Numbers below.
- **Known range:** a planning-page UI ticket that adds tests to `test_planning.py` is at the edge for the developer even at difficulty 4. f109-01 and f109-03 got there with directions; their fix ticket didn't.
- **What to change:** see "What next". A line added to `docs/task-writing.md`: a ticket whose tests build records by hand names the real record they must copy.

## Workflow observations
- The two runner fixes (procs, checks) landed between this milestone's start and main, so the review reads them too. They are small, so no harm here; bug-01 covers the general case.

<!-- runner report -->
<!-- /runner report -->
