# Review: F94, While you were away says who, when and how long, once

- **Status:** round 1 done; one small developer ticket left (f94-02), then ready for your sign-off.

## Sign-off sheet

**Expected:** your note said each row of While you were away named its agent twice, ran onto one line when the title was short, and didn't say when the ticket finished or how long it took. So each row now names the agent once, then on its first line how it went, when it finished and how long it took, and the title always on its own second line ([mock-up](../cards/f94-mockup/away-rows.html)).
**Done when:** no row says an agent's name twice; every row shows when its ticket finished and how long it took on the first line; a short title sits on its own line on a wide screen, like a long one.

### 1. What changed
- On the Overview, each row of While you were away reads, for example: **Opus** `f30-01-thread-latest-first` after 3 developer attempts · finished 06:36 · took 1.9 h, and below it the ticket's title.
- A ticket that finished on another day shows the day too: "finished 15 Oct 19:22".
- "took" runs from the ticket's first job to its finish, waits included, so a ticket that sat half a night shows it.
- A ticket the lead built in a terminal session has no name and no "how it went", only its finish and how long it took.
- One change from the mock-up, made in this review: "finished after 3 developer attempts · finished 06:36" said "finished" twice, so it now reads "after 3 developer attempts · finished 06:36".

### 2. How to test it yourself
1. Open the Overview on the laptop and pick "the last 24 h" under While you were away.
2. Check each row: the agent's name once at the start, then how it went, "finished …" and "took …", then the title on the line below, even for a short title.
3. Do the same on the phone: the title still starts its own line.
4. Find f17-01-status-dot-and-sign (built in a terminal session): no name, but a finish time and a duration. It reads "took 142.2 h" today; after f94-02 it reads "took 5.9 days".

### 3. Left for later
- **f94-02-ago-in-days** (ready, a small developer ticket): durations of two days or more read in days, here and on the tickets page's "last worked".
- Nothing goes to the backlog.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-10: planted by you; planned by the lead as one developer ticket, with a mock-up.
- 2026-10-16, 10:20 ([session report](../sessions/2026-10-16-1020.md)): f94-01 merged by the developer on its third attempt, after 2 h 43 min. Attempt 1 timed out, attempt 2 was stopped with no edit after 20 min, and the lead gave a direction before attempt 3. 10.2M local tokens; Claude for the direction only.
- 2026-10-16: this review, round 1. The code was right; four of the developer's new tests were weak, and the lead rewrote them. One wording fix, one ticket.
- Lessons:
  - **Read the page on real data, not just the diff.** Both of the review's visible findings (the doubled "finished", "took 142.2 h") came from `softfield look page /away`, not from the code or the tests.
  - **A test the developer writes for a "Done when" line has to fail without the change.** Here, the no-name test passed on rows from other tickets in the fixture. Tests that read one ticket's own row (the new `away_row` helper) avoid that.
  - **Three attempts and 10M tokens for a 30-line change** is the developer's cost on template work: two attempts did nothing useful before the direction.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** checkpoints should run the page on real data (`softfield look page …`) for UI tickets. This milestone had no checkpoint at all, and the review's best findings came from looking at the page. Text ready to paste in the Plant box: "For a ticket that changes a page, the checkpoint (or the review) reads the page on the real database with softfield look page and compares it with the card's mock-up. Open questions: in every checkpoint, or only for tickets with a mock-up? What if the database has no rows for the change?"

### 7. What clogged the factory line
- **Two lost developer attempts, about 1 h 40 min:** attempt 1 ran to its time limit and attempt 2 made no edit in 20 min, before the lead's direction got attempt 3 through. What would unclog it: for template tickets, the ticket gives the exact markup to write (the mock-up's `<li>`), so the developer's first step is an edit, not exploring. Now in `docs/task-writing.md` ("Lessons from F94").
- The runner's per-wait hours are in the block below.

## What was built
- **`AwayTicket.finished` and `.took`** (`factory_dashboard/queries.py`): the finish is the ticket's last job's end (what the list already sorts by), and "took" runs from the earliest start among all the ticket's jobs to that finish.
- **`label` without the name:** "lead ticket", "1st try", "2 attempts", "after 3 developer attempts" (after this review's F2); still empty with no `merged_by`.
- **`_partials/away.html`:** the name, the ticket link, then `class="how"` (label · finished · took) and `class="title"`; the day is shown when the local date isn't today's. `overview.py` passes `now` to both the page and the in-place partial (outside the ticket's `files:`, but needed for it).
- **`dashboard.css`:** `#away .how` in `--ink-2`, and `#away .title { flex-basis: 100% }`, scoped to the panel as the ticket asked.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | The no-merged_by test passed on other tickets' rows and never checked "no name, no label" | Rewritten on `away_row`: no `.agent`, `.how` is "finished … · took 10 min" |
| F2 | nit | claude | "finished after 3 developer attempts · finished 06:36" said "finished" twice (live page) | Label is now "after N developer attempts"; the page test checks "finished" once |
| F3 | nit | local | "took 142.2 h": `ago` has no days step | Ticket [f94-02-ago-in-days](../tasks/ready/f94-02-ago-in-days.md) |
| F4 | nit | claude | The "Opus once" and "title only in .title" tests didn't test that | Count in the ticket's own row; the title's text checked once, in `.title` |
| F5 | nit | claude | Finish-time tests used jobs out of order, didn't check "took", and broke far west of UTC | Jobs in order, "took 20 min" / "took 3 h" asserted, local day handled |

Read and found sound, no finding:
- **"took" counts every job of the ticket**, from any earlier run, as D3 wants (waits included). `away()` reads all of the project's jobs, not only the span's, so a long ticket isn't cut short.
- **`{% if t.took %}` hides a zero duration.** Only a ticket whose single job lasted 0 s, which doesn't happen.
- **`%-d`** works on Linux and macOS, the only places the dashboard runs.

Edited existing tests: five away tests in `tests/factory_dashboard/test_overview.py` changed their expected label from "Opus · …" to the label alone, as the ticket asked. None was loosened in substance, but two now checked "Opus" anywhere in the panel. F4 tightened them to the ticket's own row.

No checkpoint ran on this milestone, so there is no checkpoint finding to judge. French: no `coucou/locale/` file changed. Screenshots: no browser here; the page was read as text on the live database (`softfield look page /away`), and the layout matches the mock-up's markup and CSS. After the fixes: `uv run pytest -q tests/runner tests/factory_dashboard` gave 2320 passed (it started before F2's label change, which touches only `test_overview.py`), and `test_overview.py` gave 104 passed after it. Ruff and mypy are clean on `factory_dashboard`.

Score: 7/10. The code is small, correct and matches the mock-up. But four of the six new tests didn't test what they were named for, and the live page showed a wording repeat that the mock-up had too.

Stop reason: none. F3 is a ready developer ticket; it gets the usual checkpoint, not another review round.

## Factory
- **The flow:** one developer ticket, three attempts (timeout, no-edit stop, then a pass after the lead's direction). No escalation, no park, no checkpoint. The owner's only part was the plant.
- **Models:** qwen3.6-35b-a3b, local, 10.2M tokens in; Claude Opus for the plan, the direction and this review. Dollars in the numbers below.
- **What to change:** (1) for UI tickets, give the exact markup to write, from the mock-up, so attempts start by editing (item 7); (2) read the page on real data in checkpoints or reviews of UI tickets (item 6, card text ready to plant). (1) is now in `docs/task-writing.md`, with a "Done when names the row" lesson; (2) waits for the owner to plant it.

## Workflow observations
- The mock-up repeated "finished" too ("finished after 3 developer attempts · finished 10:32"), and nobody saw it until the page ran on real data. Mock-ups show the wording of every fact next to each other, so read them aloud once.
- The developer's tests were made to match the "Done when" lines' words, not to fail without them. A ticket's "Done when" for a page could name the row to check ("in away-x's own row") to steer that.

<!-- runner report -->
<!-- /runner report -->
