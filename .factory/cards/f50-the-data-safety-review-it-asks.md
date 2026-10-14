# Milestone F50: a finished card shows its review

> **State:** done · **Priority:** 2 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-08. Base: git tag `f50-the-data-safety-review-it-asks-start`. Report: [`.factory/reviews/f50-the-data-safety-review-it-asks.md`](../reviews/f50-the-data-safety-review-it-asks.md).
> Planted by the owner on 2026-10-08.

## Notes
The owner, 2026-10-08: "the data safety review it asks has no info".

From the code: F20 (data safety) is on the desk under "Finished, to talk through" with "every ticket merged · waits for your sign-off", and links to `/planning/f20`. Three gaps add up to an empty page:
- **It ripens too early.** `_field` in `factory_dashboard/line.py` calls a card ripe as soon as every ticket is done. F20's review hasn't run yet: it is queued ("F20's tickets are all done", status `review due`), so `.factory/reviews/f20-data-safety.md` and its sign-off sheet don't exist. The F3 and planning-room mock-ups meant ripe *after* the review ("F2 is ripe: the review is done"; "review ready").
- **The thread shows nothing of the result.** F20 was planned in a terminal, so it has no thread: the page is a title and an empty reply box. Even with a thread, `thread.html` never shows the sign-off sheet; only `/milestones/<key>` does, and nothing links there.
- **No way to act on it.** Nothing on the dashboard sends a sign-off, though `POST /requests` accepts `signoff` and the runner applies it as `runner signoff` would.

F20 itself works (checked 2026-10-08): `~/Dropbox/software-factory-backups/factory-metrics-20261008-0820.sqlite` exists, and five approved threads are in `.factory/planning/`.

### From F63: There are items finished to talk through and need my sign… (merged by the lead on 2026-10-08)
There are items finished to talk through and need my sign off apparently but I can't do anything with those, there is no sign off button. And one of them is completely empty

## Expected outcome
A card reaches "Finished, to talk through" only once its review is written. Its page then opens on what changed, how to test it and any decision waiting, and has a Sign off button.

## Done when
- With every ticket of a card merged and its review not yet written, the card isn't on the desk or the floor's Ripe; it stays in the rows with all its tickets done, and the queue shows its review.
- Once the review is written, the desk lists it with "reviewed · waits for your sign-off", and its page shows What changed, How to test and Decisions waiting for you above the conversation, with a link to the whole review.
- Sign off on that page shows at once as "signing off at the runner's next pick" (dashed orange edge) and the button goes; the runner signs it off at its next pick.

## Decisions
- **D1 Ripe means reviewed.** A card is ripe when every ticket is done and its `milestones.signoff` sheet is stored (the review loop's `_record_review`, or a report written by hand and synced). Before that it stays in the rows. No new state or column.
- **D2 The sheet on the card's page.** The thread page shows the sheet's three sections the owner acts on (What changed, How to test, Decisions waiting for you) whenever the sheet exists, rendered as the milestone page does (`_to_html`), plus "The whole review" linking to `/milestones/<key>`. The other sections stay on the milestone page.
- **D3 Sign off from the page.** A Sign off button on a ripe card's page sends `signoff` with the card's key, as Archive sends `archive`. It shows on its way at once and stops being clickable (owner, 2026-10-07). The runner's refusals stay as they are (a dirty main waits; tickets left refuse), and its result shows under the button. No score field: `runner signoff` doesn't need one.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | ripe-after-review | D | 2 | – | D1: `_field` ripens a card only with its sheet |
| 02 | thread-signoff-sheet | D | 3 | 01 | D2: the sheet on the card's page; the desk's words |
| 03 | signoff-button | D | 2 | 02 | D3: Sign off on a ripe card's page |

All in `factory_dashboard/` (not protected), each following an example in the code: developer tickets.
