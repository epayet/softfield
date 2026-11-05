# Review: F192, a fast lane request shows on the board and the Overview as soon as it's made

- **Status:** round 1 done; waiting for your sign-off and your check on a real phone.

## Sign-off sheet

### 1. What changed
- **The board shows a fast lane request at once.** After you pull the lever, the card says "fast lane · on its way · at the runner's next pick" on a dashed plate. Pulled off, it says "leaving the fast lane · on its way". Once the runner has taken it, you get the plain "fast lane" plate, or none.
- **The back button shows the board as it is now,** on a phone too, with no reload. Moves you haven't sent are kept, and nothing is fetched while you have any.
- **The Overview says the same.** The "Fast lane:" line names the card, "on its way", and Next in line already puts its tickets in the lane's bay, each row marked. A card asked out says "leaving · on its way", and its tickets go back among the rest.
- **The bug this review stopped:** as merged, pressing back on a phone blanked the whole board. It's fixed, and a test now covers it on a phone.

### 2. How to test it yourself
The tests can't produce a real restore from a browser's memory, so step 2 is the check that counts.
1. On your phone, open the board, then a planted card's page.
2. Pull the Fast lane lever and press back. The board should show the card with the dashed plate, in the stage you were looking at, with its grip and ⋯ working.
3. Open the Overview. The card should be named under Claude's meters, "on its way", with its tickets in the lane's bay.
4. After the runner's next pick, reload the board: the plain "fast lane" plate. On the Overview, "on its way" is gone.
5. Pull the lever off and repeat: "leaving the fast lane · on its way", then no plate.
6. Drag a card on the board without sending, open any card's page and press back. If the phone restores the page, your move is still there, not sent. If it loads the page again, the move is lost, as it was before this card.
7. In the light theme, check that the on-its-way words are easy to read. I changed their colour from the token values and haven't seen it on a screen.

### 3. Left for later
- **bug-60:** stop a local attempt that keeps repeating the same failing tool call. It's set aside on the board as a seed.
- **A very quick drag:** starting a drag in the moment between pressing back and the fetch answering loses that drag. On home Wi-Fi that moment is a fraction of a second, so I left it.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-04 08:53 ([session](../sessions/2026-11-04-0752.md)): `f192-01` merged on Qwen's last attempt, after two failed attempts and a direction from Opus. The checkpoint passed it.
- 2026-11-04 22:07 ([session](../sessions/2026-11-04-2202.md)): `f192-02` merged on Qwen's second attempt, after a 77-minute timeout. `f192-03` was escalated after three failed attempts, and the lead finished it on its branch.
- 2026-11-05: review round 1 found three blocking bugs, all in `f192-02`, and fixed them itself, along with three smaller points. One more went to bug-60.
- Lessons:
  - **All the gates passed on a blank page.** `f192-02`'s test only counted buttons, and hidden buttons still count. It also skipped the "second body" the ticket asked for. A redraw's test now has to show the new thing, visible, at phone width: note 3 in `.softfield/developer.md`.
  - **The ticket lost half a decision.** D3 covers back with or without the browser's memory; the ticket's Done when covered only the first. A ticket's Done when has to carry every branch of the decision it cites. That was the lead's slip, and it's in ADR 02's log.
  - **Sharing one function changed the other caller.** The send path lost its reload when it moved into `refresh()`, and nothing tested that path. It's back, with a test.
  - **The subject of a `reserve` request cost `f192-03` two attempts.** It's the short key, as note 2 in `.softfield/developer.md` now says.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** plant a card so that any request sent from a page shows on the page you go back to, as this one now does. The back-button redraw is only on the board today; the same stale page can appear on other pages.
- **Factory:** make the layout check or the browser tests run a page's redraw at phone width as a standard step, so that "blank after redraw" can't pass again. I'd do this only if it happens a second time.

### 7. What clogged the factory line
- **Failed local attempts took about 3.9 hours.** The whole milestone used 4.8 hours of Qwen's time, and these attempts merged nothing: `f192-01` 30 minutes, `f192-02` 77 minutes, `f192-03` 127 minutes. To unclog it: note 2 stops the `reserve` mistake from happening again, and bug-60 stops a looping attempt sooner.
- **`f192-02` waited 12 hours for its turn** (10:05 to 22:07 on 4 November). Other cards ran first, and about 7 hours of that had nothing running after Claude's login expired, which bug-59 has since dealt with.
- **The card itself waited over 2 days from planting** (2 to 4 November), which is the board's order working. There's nothing to change.

## What was built
- `factory_dashboard/board.py`: `Card.lane_asked`, the latest open `reserve` request of a card in a `RESERVABLE` stage (D1). `reserve_marked` also returns a card asked in (D4).
- `factory_dashboard/templates/board.html` and `dashboard.css`: the plate with its dashed edge, separate from a reorder's (D2).
- `factory_dashboard/static/board.js`: `refresh()`, the one redraw used after a send and on the way back, and the `pageshow` listener (D3).
- `factory_dashboard/overview.py`, `_partials/allowance.html`, `_partials/queue.html`: the "Fast lane:" line and Next in line follow the request as the runner will (D4). The runner and the card's doc don't change.
- `tests/factory_dashboard/test_board.py`, `test_overview.py`: the tests, reworked by this review as below.

No French changed: the dashboard has no translations. The card's after pictures: none.

## Findings and resolutions
| id | severity | route | summary | resolution |
|----|----------|-------|---------|------------|
| F1 | blocking | claude | On a phone, back from the browser's memory blanks the field: the redrawn columns never got `.shown` | Fixed: the same steps as after a send, including `show()` |
| F2 | blocking | claude | That path gave cards a stage by position in the old line, and ignored the fresh `#board-line` | Fixed: one `refresh()` with no skip argument; found by reading the code, and the test now checks each stage's order |
| F3 | blocking | claude | Back without the browser's memory fetched nothing, against D3 | Fixed: reads navigation type `back_forward`; tested with a document that answers its old copy |
| F4 | should-fix | claude | A failed refetch left "Sending…" after a sent order; an error answer put "null" where the field was | Fixed: `refresh()` changes nothing unless a board came, and send reloads when it doesn't |
| F5 | should-fix | claude | `f192-02`'s tests couldn't see the plate or a blank field, and one didn't check its own name | Fixed: rewritten to show the visible plate on a phone; note 3 in `.softfield/developer.md` |
| F6 | should-fix | claude | The on-its-way words were hazard yellow on pale plates in the light theme | Fixed with `--warn-ink`; not seen on a screen |
| F7 | nit | claude | No test for the Overview going back to plain | Added |
| F8 | should-fix | later | A local attempt looping on one failing call isn't stopped | bug-60 |

**Tests read closely:** the only existing test edits are this review's own, to `f192-02`'s tests. The developers added to `test_board.py` and changed no older test. Four browser tests, three new and one rewritten, failed before the fix and pass after it.

**Checkpoint:** one, on `f192-01`, which found nothing. It should have caught the plate's half of F6, which was in the diff it read. It never read `f192-02` or `f192-03`: since F162, no checkpoint runs on merges the review is about to read, so this review was their first reader, and it caught them.

## Factory
- **Flow:** no stops for you, and no interventions. Two directions and one escalation. Claude's limit and the expired login delayed the line, not this card's work directly.
- **Models:** Qwen merged 2 of 3 tickets, none on its first attempt. The plate and the Overview's templates were close; the redraw's logic was wrong and its tests didn't show it. Opus's directions took about a minute each, and its escalation 11 minutes.
- **What to change:** "fail without the change" passed on `f192-02` because the test failed for a smaller reason than the feature, a missing fetch. The fix for that is in the notes and ADR 02's log. Two local attempts timed out at about 77 minutes, after 48 and 56 steps, so about 1.4 minutes a step, each carrying roughly 80,000 tokens of context. That points to long attempts rather than a stalled model; the merged attempts took 11 to 30 steps. My suggested fix is to leave the model's settings alone and route a ticket likely to need more than about 30 steps to the lead, as below.
- **Who built it:** a redraw across a page's script at difficulty 4 was too much for the developer. With hindsight, "the lead directly" was the cheaper route for `f192-02`.

<!-- runner report -->
<!-- /runner report -->
