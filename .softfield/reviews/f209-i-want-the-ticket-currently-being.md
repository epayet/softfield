# F209: the work that runs now, on the board — review

- **Status:** done, signed off by the owner on 2026-11-13.

### 1. What changed

- On the board, the card something works on stands out: a thick frame, a filled "Working now" head with a breathing lamp, and a light wash, in orange when the lead works and in blue when a developer does. The old small "Now:" line is gone. A job waiting for Claude's limit keeps the frame, says "Waits for Claude until 23:40" and doesn't glow. In the developers' view a card at work no longer fades.
- A review, or the lead answering you on a card's conversation, now lights that card too. Before, only ticket work lit a card, and only in Planted.
- A plate at the top of the board, above the stage counts, says what works now: the card, the ticket and its goal, who, which attempt and for how long, and its place ("#23 in Planted"). Tap it to open the card, or the conversation when the lead is answering you. It shows even when a search hides the card. With nothing running, one quiet line says so.
- The board updates itself every 10 seconds, and as soon as you come back to the tab. It doesn't refresh while you drag a card, have the ⋯ menu open or have moves you haven't sent. The plate then says "Refresh held: your moves aren't sent yet", or "Not updated since 20:14" when the dashboard doesn't answer.

Matches the mock-up, except that the sample data behind the after pictures had no live job. They show the quiet "Nothing is being worked on now" line and no lit card, so the lit states were checked against the mock-up in the code and the tests. Two small differences were fixed in this review: the plate was a frame inside a frame, and the conversation row said "open the card".

### 2. How to test it yourself

1. On your phone, open the board while the runner works on a ticket. The plate sits above the stage counts and names the card, the ticket and "Working now · a developer" (blue) or "· the lead" (orange). The lamp breathes.
2. Tap the plate. It opens that card. Go back.
3. Pick the stage the card is in. The card has the coloured frame and the "Working now" head, and keeps its #place.
4. Search for a word that isn't in the card's title. The card leaves the field, but the plate still shows it.
5. Leave the board open and wait for the runner to move to its next ticket. Within about 10 seconds the plate and the card follow, and you don't have to reload. The stage you picked stays picked.
6. Drag a card and don't send. The plate says "Refresh held: your moves aren't sent yet". Press Cancel and it says "refreshes every 10 s" again.
7. Switch to the developers' view. The card at work is at full strength, even if it would otherwise fade.
8. When you write on a card's conversation and the lead answers, the plate says "Working now · the lead answers you" and opens the conversation.

### 3. Left for later

Nothing from this card. No bug tickets were set aside.

### 4. Decisions waiting for you

None.

### 5. How the work went

- 2026-11-06, then 2026-11-10 ([session](../sessions/2026-11-10-0229.md)): f209-01. The local model made no usable edit in two 20-minute attempts, nor in a third after direction. The lead finished it on its branch.
- 2026-11-11, then 2026-11-12 ([session](../sessions/2026-11-12-0000.md)): f209-02. Two 20-minute attempts with no edit, then a direction from the lead (parked a while for Claude's reset), then the local model built it in a 60-minute last attempt. It merged as the local model's work.
- 2026-11-12, then 2026-11-13 ([session](../sessions/2026-11-13-0046.md)): f209-03. Two 20-minute attempts with no edit, then a 75-minute last attempt that timed out with unusable script and tests that couldn't fail (`assert True`). The lead rewrote it in 44 minutes.

Lessons:
- **Big test files stall the local model.** On all three tickets, the first two attempts spent their 20 minutes reading the 3,000-line `test_board.py` and the whole `dashboard.css`. The f209-03 lesson ("edit first, read later") went into `.softfield/developer.md`.
- **Tests that can't fail now stop a ticket.** f209-03's tests passed their gates with `assert True`. The gates now refuse an assertion that can't fail, in any test folder (`runner/gates.py`, `_CANT_FAIL`).
- **A page script that redraws itself is lead work.** Two of the three tickets ended with the lead. Browser state, hold rules and node identity are beyond what the local model handles today.

### 6. What next

- **Product:** nothing for now. Product work is on hold until you ask.
- **Factory:** route browser-script tickets (polling, drag, a redraw that keeps the page's state) straight to the lead. Each one here cost two dead 20-minute local attempts and a day's wait for direction before anyone wrote code. Next, the plate could be a Floor element on the Overview too, so the same "what works now" shows on the first page you open.

### 7. What clogged the factory line

From the `jobs` table:
- **Failed local attempts:** 6 × 20 minutes with no edit, plus f209-01's failed last attempt (20 min) and f209-03's timed-out one (75 min). That's about 3.6 hours of the local model on nothing. To unclog: route browser-script tickets to the lead (above), and use the new "first edit within ten steps" developer note.
- **Waits for direction:** after the second failed attempt, a ticket waited for the lead's direction: f209-01 for about 87 hours (Nov 6 → Nov 10), f209-02 for about 12 hours (parked for Claude's 5-hour window), and f209-03 for about 16 hours. The runner did other cards in between, so this was this card's own delay, not idle machines. To unclog: the same routing, so these tickets never queue for direction.
- No stops for you, and no tickets idled on one another: f209-02 and f209-03 waited on their predecessor by design, and each started within a day of it.

---

## What was built

- **f209-01-card-at-work** (lead after escalation): `Work` became the live job of any card (`at_work`, its oldest live job), with who works (lead or developer, the top-bar dot's rule), its role, elapsed time and Claude-limit wait. A review or a planner lights the card its milestone names. The CSS adds the frame, head, lamp and wash, and outranks the developers' view's fading. Tests cover each role, the waiting state, bugs, the legend, and computed colours in the browser.
- **f209-02-plate-working-now** (local model): `Board.now` is built from all cards before search and kind narrow. The plate at the top has the right wording per role and links to the card or the conversation.
- **f209-03-field-refreshes-itself** (lead after escalation): `board.js` fetches the board every 10 s and when the tab comes back. It swaps only the parts whose text changed (plate, stages, line, plot counts), so unchanged nodes stay in place. A drag, unsent moves, the ⋯ menu or `liveIdle` hold it, and an answer that arrives during a drag is dropped. The plate's small line says held, or not updated since when. It also added the gate against assertions that can't fail.

## Findings and resolutions

| id | grade | what | resolution |
| --- | --- | --- | --- |
| F1 | should-fix | The plate was drawn inside a second plate (`section.board-now` around `a.board-now`); `.lead`/`.developer` set `--who` page-wide; `@keyframes breathe` was defined twice | Fixed by the lead: the section is a plain `board-now-rows` grid with jobs and the idle plate without; `--who` is scoped; the duplicate is removed; a test checks the section's class |
| F2 | should-fix | The planner row said "open the card" and its link dropped `?project=`; its test matched the card's own conversation link and could not fail | Fixed by the lead; the test now reads each plate row's link, project and words |
| F3 | nit | Titles were cut at 40 characters mid-word with no "…" | Fixed by the lead: `truncate(40, True, '…', 0)` |

Checkpoint finding C2118-2 (plate row nested in a same-class section): confirmed, and the same as F1. F2 was in the diff the checkpoint read and was missed.

Tests read: f209-02 edited two existing tests in `test_app.py`, adding the new lamp to the breathing list and to the radius exceptions. Both edits are legitimate. Its own tests check content, not just presence, except for the planner link (F2). f209-03's browser tests use the page clock, check node identity, the hidden tab, drag, menu and `liveIdle` holds, and the failure clock. They're thorough. No French text was touched; the dashboard has no translations.

## Set aside

Nothing.

## Workflow observations

- Every ticket's first two local attempts died at the 20-minute no-edit cap. That points at ticket routing for page-script work, not at the model's speed.
- The checkpoint caught the nested plate but graded it a nit. Against the mock-up it was a visible difference.

<!-- runner report -->
<!-- /runner report -->
