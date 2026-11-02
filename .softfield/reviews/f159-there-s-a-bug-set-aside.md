# Review: F159, a set-aside ticket says it won't run, with a Queue it button on its page

- **Status:** done, signed off by the owner on 2026-10-23.

## Sign-off sheet

### 1. What changed
A ticket that is set aside now says so where you meet it. Its board card reads "Set aside, won't run until you queue it ›" in the action look, not as a grey note. The page it opens starts with a "Set aside" plate (hazard stripe, corner ticks): "This ticket won't run until you queue it.", a line saying where it joins the line, and a yellow **Queue it** button. Pressed, the plate shows "Queue it · on its way · at the runner's next pick" at once, and still does after a reload until the runner has moved the ticket. Every ticket's page now shows its Goal as a paragraph and Done when as a list, with the lead's notes folded under "The lead's notes for the agent", and no front matter (`id:`, `priority:`…). The State line reads "set aside" instead of "later".

bug-03 (the old roadmap's items as seed cards) was queued when you approved the plan on 2026-10-20 and is in the ready line now.

### 2. How to test it yourself
1. On your phone, open the board. A set-aside bug in the Seed column (if any is left) reads "Set aside, won't run until you queue it ›". Tap it.
2. The page starts with the Set aside plate and the Queue it button. Press it: the button goes and the dashed "on its way" line shows straight away, with "Asked: the runner will do it." under it.
3. Reload the page: it still says on its way, with no button. After the runner's next pick, the ticket's state reads "ready" and the plate is gone.
4. Open any ticket, for example `/tickets/bug-03-roadmap-items-to-seeds`: Goal as text, Done when as a list, the notes folded, no `---` lines.

If no bug is set aside when you test, the Tickets page's Set aside table lists any other set-aside ticket; its id opens the same page.

### 3. Left for later
- The folded notes and the Goal still run their lines into one paragraph (bullets included). Ticket `f159-02-ticket-notes-keep-their-lines` fixes it next.
- In `docs/backlog.md`: one test that checks every button's target exists on its page (the slip below), and markdown shown as typed (backticks, bold) until the dashboard renders markdown.
- D4: no "throw away" button for a set-aside ticket, as planned.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-20: planned in the Planning room from your note; plan approved at 21:08, which queued bug-03 and f159-01.
- 2026-10-23 03:28 ([session](../sessions/2026-10-23-0328.md)): 1 ticket, `f159-01-set-aside-ticket-page`, built by the local model in 65 minutes, first attempt, 8.6M local tokens, no Claude cost.
- Lessons:
  - The local model built the plate, the parsing and the tests well, but the button it wrote **could never send**. It pointed at a place on the page that only appeared after sending, and htmx refuses to send then. Every test passed because they read the markup only. The review fixed it and added a test. A general check is in the backlog.
  - It moved the board's wording into the template and deleted a test line instead of changing the words in `board.py` as the ticket said. The review put it back.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** the slip in this card is the kind a test can't see unless it presses the button. A small dashboard test that checks every button's `hx-target` exists on its page would have caught it for every page at once. It's in the backlog; I'd plant it as a card if a second button slips the same way. Developer tickets with a button could also say "the target must exist before the press" in their Context; I've done that by example here.

### 7. What clogged the factory line
- The plan waited 2 days 6 hours in the line (approved 2026-10-20 21:08, started 2026-10-23 03:29) behind cards placed above it on the board. Nothing sat idle: the factory merged other cards' tickets throughout (runs 350–437). Nothing to unclog: that is the board's order working.
- The build itself was one 65-minute local job with a 57-second cold model load, first attempt; no limit waits, no stops for you.

## What was built
- `factory_dashboard/tickets.py`: `parse_ticket_body` drops the front matter and reads `### Goal`, `### Context`, `### Done when`. `ticket_page` sets `is_later`, `on_its_way` (an open `queue` request names the ticket) and the priority the ticket would join the line at.
- `templates/ticket.html`: the Set aside plate first (D2), the Queue it button posting the existing `queue` request to `/requests` (D1, nothing in `runner/` changed), the parsed Goal and Done when (D3), "set aside" on the State pill.
- `templates/board.html`, `board.py`: the set-aside bug card's note in the `card-action` look with the new words.
- `static/dashboard.css`: the plate's look from the mock-up, existing tokens only (hazard, ink, plate, rule).

Tests: three for the parser; the plate, the button, the State pill, the parsed body, the folded notes, the on-its-way state and no plate on other tickets. Edited existing tests: `test_board.py`'s two set-aside bug tests now expect the new words. One of them had lost its `bug.note` assertion; restored (F3).

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | blocking | claude | Queue it sent nothing: its `hx-target` existed only once the request was on its way, and htmx sends no request to a missing target | Fixed: the target and the on-its-way line are always there; the press marks the plate sent at once, as the mock-up does; new test |
| F2 | should-fix | local | Goal and the notes run into one paragraph, bullets included | Ticket `f159-02-ticket-notes-keep-their-lines` |
| F3 | nit | claude | The board words were hard-coded in the template, `SET_ASIDE` kept the old ones, a test assertion was dropped; the open-request lookup re-wrote `metrics.open_requests` | Fixed |
| F4 | should-fix | backlog | No check catches an `hx-target` that names nothing on the page | `docs/backlog.md` |
| F5 | nit | backlog | Parsed text shows markdown as typed | `docs/backlog.md` |

No checkpoint ran on this milestone, so there are no checkpoint verdicts. Score: 6/10. The page, the plate, the board card and the parsing match D1–D3 and the mock-up, but the one thing the owner asked for, a button that queues the ticket, didn't work as merged.

Checked and fine: the live `/tickets/bug-03-roadmap-items-to-seeds` shows the parsed Goal, Done when and folded notes with no front matter; the plate's CSS adds no colour; a ticket in any other state has no plate. With the review's fixes, ruff, mypy, `tests/runner` (1,685 passed) and `tests/factory_dashboard` (905 passed) are green. The two folders were run apart, since together they take longer than one call allows (see the f172 backlog item). A first combined run showed two failures; my board edit landed while it was running, and they didn't come back in the clean runs.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Two items added to `docs/backlog.md` (F4, F5).

## Factory
- Flow: planned 2026-10-20, built 2026-10-23 by one local developer job, first attempt, gates green, no stops, no limit waits, no parks. No checkpoint ran.
- Models: the local model (8.6M tokens in, 32.9k out) did the whole build. Claude's cost was the planning and this review.
- What worked: the mock-up and the ticket gave the developer the exact words and look, and it reproduced them closely.
- What didn't: the developer kept only the button's markup from the worked example (the Tickets page's Queue button, whose target always exists) and moved its target into a branch. Gates and tests can't see a dead htmx button. What to change: the backlog check (F4). Meanwhile, when a ticket has a button, the lead's Context should name the element its answer lands in, and that it exists before the press.
- The session report flagged a file changed outside `files:` (`board.html`). That was the ticket's own Context asking for it: the lead should have listed it. A ticket-writing slip, not the developer's.

<!-- runner report -->
<!-- /runner report -->
