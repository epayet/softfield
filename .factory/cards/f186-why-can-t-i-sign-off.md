# Milestone F186: A sign-off stays signed: F142's keeps coming back

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-29.

## Notes
Why can't I sign off f142 it keeps coming back

## What happens today (from the code and the database, 2026-10-29)
- **The first sign-off worked, and a review finishing after it undid it.** The owner asked at 08:37 on 2026-10-28 (request 882) while F142's review was in its round 2. The runner applied it at 08:53:56, in the same second as round 2's commit: `dd2f7e6` marked the card done, tagged `f142-…-done` and resolved the item. The review then ended, and `_review` in `runner/cli.py` ran `owner.verdict` anyway: at 09:00:00 (`f66e9f5`, "runner: milestone verdict") it wrote "READY FOR SIGN-OFF", `_record_review` (`runner/milestone.py`) set the milestone's status back to `review`, and `metrics.upsert_owner_item` reopened the sign-off item (it sets `resolved = NULL` on a resolved one). That is item 250, open since.
- **Every sign-off since fails on the tag.** `owner.signoff` (`runner/owner.py`) writes the doc and commits first, then runs `git tag <key>-done`, which exists, so it raises before `_signed_off` touches the database. Requests 890, 910, 921 and 929 each ended "tag … already exists", and the item stayed. `a0de65e` is one of them: it only changed the date to 2026-10-29.
- No other card is caught this way: of the six open sign-off items, only F142's milestone is already signed off.

## Expected outcome
- A sign-off stays signed: a review or verdict ending after it neither reopens the item nor sets the milestone back to review.
- Pressing Sign off on a card already signed off settles it (item resolved, milestone done) instead of failing.
- F142's sign-off leaves the desk on its own, without another press.

## Done when
- f186-01 merged.
- To test: after the runner's next pick, the Overview no longer asks for F142's sign-off (Phone notifications), and F142's milestone page says done.

## Decisions
- **D1: a signed-off milestone gets no verdict.** After a review, `_review` (`runner/cli.py`) checks `signed_off(repo, key)` (`runner/milestone.py`) and, when it is, records nothing more: no `review` status, no verdict, no owner item.
- **D2: a second sign-off settles, quietly.** When the milestone is already signed off, `owner.signoff` writes no file, makes no commit and no tag, and still runs `_signed_off` (status done, items resolved). The first sign-off's date stays.
- **D3: the runner heals what is already wrong.** Where the runner applies the owner's requests before a pick, an open `signoff` or `review-stop` item whose milestone is signed off is resolved and its milestone set to done. That clears F142 with no press.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | sign-off-stays-signed | L | 3 | – | D1, D2, D3 |

The lead's: `runner/` is protected. No mock-up: nothing on a page changes, the sign-off just stops coming back.
