# Review: F198, Plant an idea stays at the top, with Coming seeds under it

- **Status:** done, signed off by the owner on 2026-11-11.

## Sign-off sheet

### 1. What changed
On the Planning page, the Plant an idea box now comes right under the two tiles (The factory now, The lead's window), and it stays there. When you plant something, it shows in Coming seeds just under the box, instead of above it pushing the box down.
- **Wide screen:** Coming seeds sits in the box's column, beside Your desk, so neither the box nor the desk moves when a plant arrives or leaves.
- **Phone:** Coming seeds comes between the box and Your desk. The box stays put; the desk moves down while a plant waits.
- With nothing on its way, the page looks as before.

No after pictures for this card, so there was nothing to compare against the mock-up.

### 2. How to test it yourself
1. On your phone, open Planning. The Plant an idea box is right under the two tiles.
2. Type a note and press Plant. The box stays where it was, empties, and your note shows in Coming seeds just under it.
3. Start typing a second note and leave it for a while (over 5 seconds). Your words are still there.
4. On a wide screen, do the same: Coming seeds appears under the box, and Your desk on the right doesn't move.
5. Once the runner takes the plant, Coming seeds goes away and the box doesn't move.

### 3. Left for later
Nothing. No bug tickets were set aside.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-02: the lead planned the card (Opus, about $1.07).
- 2026-11-06 ([session](../sessions/2026-11-06-0111.md)): two local attempts, about 68 minutes each, both failed the full test run. The ticket was then parked until Claude's reset, to get the lead's direction.
- 2026-11-10 ([session](../sessions/2026-11-10-0229.md)): the lead's direction (Opus, about $0.54), then the local model's last attempt merged it in 28 minutes. All the building was local.
- 2026-11-11: the lead reviewed it (round 1) and rewrote two of the new tests.

Lessons:
- The layout change was right first time it passed; the weak part was the tests. One waited 5 seconds for a refresh that never happens while the box holds words, so it proved nothing. Tests that wait for a poll need to make the refresh happen, not wait for it.
- The ticket asked for a CSS change but didn't list the CSS file. The runner flagged it; no harm done.

### 6. What next
- **Product:** product work is on hold until you ask.
- **Factory:** a test that only waits (`wait_for_timeout` of seconds) for a poll is a smell worth a checkpoint question: "does the thing waited for actually happen in this state?". Here the page's own idle rule stopped the poll.

### 7. What clogged the factory line
- **About 3 days 18 hours parked (6 Nov 10:28 to 10 Nov 04:18)** waiting for the lead's direction while Claude was limited. To unclog: F191 already lets developer work carry on during a limit; this one ticket simply had nothing to do without direction.
- **About 2 h 15 min on two failed local attempts** (jobs 1891 and 1892, 5.7M tokens in) for a difficulty-2 layout move. To unclog: F195's work on the local model's speed.

---

## What was built
`factory_dashboard/templates/planning.html`: Coming seeds (`#live-desk-coming`) moved from above the row into a new `.plant-column`, the row's first child, under `#plant-row`; Your desk stays beside it. The box and Coming are still drawn again separately, so a Coming refresh never touches a half-typed note. `dashboard.css`: the new column takes the form's old flex share and stacks its children with a 14 px gap; `.desk-coming` lost its top margin. (commit `de1f66e98`)

Tests: the order test now reads Plant, Coming, desk, Archived; three browser tests check the box stays put, Coming sits under it at both widths, and a half-typed note survives a Coming redraw. Two existing tests in `test_coming.py` got a taller window, so opening a waiting plant doesn't scroll (a scroll pauses the page's refresh for 10 seconds and would break what they check). That edit is sound.

## Findings and resolutions
- **F1 (should-fix, fixed by the lead):** two of the new tests didn't test what they claimed. The half-typed test waited 5.6 s for Coming's poll, but the poll waits while the box holds words, so it never ran. The stays-put test checked 1280 px second on the same data, with Coming already showing before it measured. Now the stays-put test runs once per width from an empty Coming, and the half-typed test stores a second plant, redraws Coming the way the poll does, and waits until both show. It also no longer waits 5 seconds. `tests/factory_dashboard/test_planning.py`.
- **F2 (nit, report only):** the ticket's `files:` left out `dashboard.css`, though its Context asked for a CSS change. A planning slip.
- **F3 (nit, report only):** `.plant-form`'s `flex: none` does nothing now (its parent isn't a flex box), and the moved block's indentation is uneven.

No checkpoint ran on this ticket, so there is nothing to judge or count as missed.

No French: the change has no wording.

## Workflow observations
The plan was precise (which element moves where, which rules move, what must stay separate) and the change itself matches it. It still took three local attempts and almost four days parked. The tests were the weak point again, as in F193: the developer wrote tests shaped like the Done when, without checking they could fail.

<!-- runner report -->
<!-- /runner report -->
