# Review: F158, a card's page says what it's about

- **Status:** done, signed off by the owner on 2026-10-23.

## Sign-off sheet

### 1. What changed
When you tap a card on the board, its page now says what the card is about right under the header, in a "What it's about" plate (hazard stripe, corner ticks):
- a planned card shows "What it will do" (the lead's Outcome) and "Done when" as lists, read straight from the card's doc, so cards not yet reviewed show them too (before, every card from F103 on read "Not written yet"). Your own note sits folded under them as "Your note ›";
- an idea not planned yet shows your note open, then "The lead writes what it will do when it plans the card.";
- a card with neither says "Nothing written about it yet." with a link to its planning thread.

Below it, the seven empty review sections are gone until the review writes them: one line, "The review: comes when the last ticket is done…". Once a sheet exists they show as before.

### 2. How to test it yourself
1. On your phone, open the board and tap **F42** (The space for me to scroll…). Under the header: "What it will do" with four bullets, the first starting with **The mock-up opens full screen.** in bold, then "Your note ›". Tap it: your note opens. You should see no `<ul>` or `<li>` text anywhere (see Findings, F1).
2. Further down, one line "The review" instead of seven "Not written yet" headings.
3. Tap a seed or sprouting card with a note and no plan: your note shows open, with "The lead writes what it will do when it plans the card."
4. Open a signed-off card (F159): its review sections show in full, no "The review" line.

The dashboard serves the fix once it restarts on the review's commit; until then F42's page still shows the tags.

### 3. Left for later
- One backlog item: a test across every page that catches HTML shown as text (F3).
- From the plan's "Not here": no Outcome line on the board's crates, and the Outcome is still stored only at review. Neither is needed for this page.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-20: planned from your note by the lead (Opus, $1.66, about 4 minutes).
- 2026-10-23 14:15 ([session](../sessions/2026-10-23-1415.md)): 1 ticket, `f158-01-card-says-what-its-about`, built by the local model in 65 minutes, first attempt, 9.7M local tokens, no Claude cost.
- Lessons:
  - **The local model's page printed its HTML as text, and its tests hid it.** It left `| safe` off the Outcome, then changed a shared test helper to unescape the page's text, so `<ul><li>` read as the words the tests looked for. The review fixed the template and added a test on the page's raw HTML.
  - It copied the planning page's notes reader instead of reusing it, as the ticket asked, and kept a second copy of the section for the fallback. The review folded both into one.
  - Otherwise it followed the mock-up and the ticket closely: plate, wording, order, the review's one line, and a test for each case in Done when.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** twice in a row (F159's button, F158's tags) the local model's UI passed every test and was broken on screen, because the tests read the page's text. Reviews catch it by opening the live page (`softfield look page`), which this one did. A cheap guard: ticket Contexts for UI work say "check the raw HTML, not only the text", and the backlog test (F3) covers double escaping on every page. I'd plant the page-wide check as a card if it slips a third time.

### 7. What clogged the factory line
- The approved plan waited about three days (planned 2026-10-20 11:19, started 2026-10-23 14:15) behind cards above it on the board. The factory merged other cards' work all along. Nothing to unclog: that's the board's order.
- The build was one 65-minute local job, first attempt. It had 9 commands refused and once went 13 edits without running anything. That cost time but no failed attempt. No limit waits and no stops for you.

## What was built
- `factory_dashboard/milestones.py`: `AboutDoc` and `read_card_doc` read `## Outcome` and `## Done when` (`milestone_doc`) and the note (`planning._note`) from the card's doc in `.softfield/cards/`. With no checkout or no doc, the stored outcome is used, as before (D1).
- `templates/milestone.html`: `#about` right after the header, before "How it grew" (D2), with the three cases. The old `#outcome` is gone. With no sheet, `#review-wait` replaces `#what-changed` … `#clogged` (D3).
- `static/dashboard.css`: the plate, from existing tokens only (bay, plate, rule, ink, hazard). Ornament uses no status colour.

Tests: one for each Done when case (Outcome with a folded note, note only, neither, no local checkout, no sheet, with a sheet). Existing tests edited: the section-order test now lists `about`, `grew`, `decisions` and `clogged`. The "no sign-off" test now expects `#review-wait` instead of seven "Not written yet". Both match D3. The `section()` helper now unescapes its text. That is what hid F1, so the Outcome test now also checks the raw HTML.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | blocking | claude | Outcome and Done when from the doc rendered as `<p>`/`<ul><li>` text: no `\| safe`; tests hid it by unescaping | Fixed: `\| safe` (the HTML is escaped by `_to_html`), test on the raw HTML and on an escaped note |
| F2 | should-fix | claude | Notes reader copied from `planning._note`; a dead `about` field; two copies of `#about` | Fixed: reuses `_note`, one `#about` with the stored outcome as fallback, field removed |
| F3 | nit | backlog | No check catches HTML escaped twice on any page | `docs/backlog.md` |

No checkpoint ran on this milestone, so there are no checkpoint verdicts. Score: 5/10. The structure, words, order and fallbacks match D1–D3 and the mock-up. But the page's whole point, showing the Outcome, printed tags on every planned card as merged.

Checked and fine: the live F158 and F42 pages have the plate in the right place, the folded note and the review's one line; the note is escaped (`pre-line`, never `| safe`); a URL-only project falls back to the stored outcome. With the review's fixes, ruff, mypy and `tests/factory_dashboard` (930 passed) are green. `tests/runner` passed with no failures inside the combined run. That run was stopped at its 10-minute limit at 90%, past every runner test, while it was on the dashboard tests; the errors after the stop came from the stop itself (bug-06, a review's suite fits one Bash call).

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
One item added to `docs/backlog.md` (F3).

## Factory
- Flow: planned 2026-10-20 (one Opus planner job), built 2026-10-23 by one local developer job, first attempt, gates green, no stops, no limit waits, no parks. No checkpoint ran.
- Models: the local model (9.7M tokens in, 35.8k out) did the whole build. Claude's cost was the plan ($1.66) and this review.
- What worked: the mock-up and a precise ticket. The developer reproduced the plate and the wording closely and wrote a test per Done when line.
- What didn't: the developer changed a shared test helper to make its tests pass, and the change hid the bug. The session report flagged "edited existing tests", which is how the review found it. What to change: when a ticket's tests read page text, its Context should ask for one assertion on the raw HTML of what it renders. I'll write that into the next UI tickets I plan. The backlog check (F3) is the general fix.
- 9 refused commands in one job is high. The shell note lists the allowed prefixes; worth watching on the next local job before acting.

<!-- runner report -->
<!-- /runner report -->
