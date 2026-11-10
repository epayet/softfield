# Milestone F231: Triage the set-aside bugs, and a Remove button for the ones not worth a run

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-06.

## Notes
There are many bugs in the seed board row and I can't do anything about them apart from queuing. Tell me which ones are worth queuing and add a way to get rid of the rest

### From F174: Which bugs are set aside in the Seed column, and which to queue (merged by the lead on 2026-11-09)
What are all the bugs set aside on the seed column

What was said on F174's thread:
You asked which bugs were set aside in the Seed column (2026-10-23). The lead listed the 43 from the old backlog file in groups. It recommended queuing bug-05, bug-06, bug-07 and bug-44, offered a bug-48 for flaky tests (it became bug-49), and asked whether to fold the bugs into one plate in the Seed column, add a filter, or leave it. That question was never answered, and the thread was archived on 2026-10-26. F231 now settles it: most of those bugs are removed instead.

## Outcome
The Seed column holds the owner's ideas and the few bugs worth a run. Every set-aside ticket's page has Remove beside Queue it, so the owner can clear one without asking the lead.

## What happens today
- 56 bug tickets sit in the Seed column (bug-05 to bug-62), all set aside in `.softfield/tasks/later/`. 43 came from the old backlog file in one pass (f5-13, 2026-10-23), the rest from reviews since. F174 listed them on 2026-10-26; four were picked to queue and none was.
- A set-aside ticket's page has one button, Queue it (`factory_dashboard/templates/ticket.html`). A seed card has Remove seed on its thread (`drop_seed`, f6-17), but a ticket has nothing like it.
- The runner already marks a ticket row `removed` when its file leaves `.softfield/tasks/` (`remove_missing_tickets` in `runner/metrics.py`), so it leaves the board by itself.

## The triage (2026-11-09, checked against main)
- **Queued with this plan (7):** bug-56 (every review stops after one round, because an old M3 finding sits at 3), bug-06 (a review can't see the test suite finish), bug-49 (two flaky timing tests that buy Opus step-ups), bug-57 (pre-flight keeps two-page tickets from developers), bug-54 (`softfield init` silently turns off a repo's own hooks), bug-07 and bug-51 (two dashboard tests that catch broken buttons and escaped markup; developer tickets).
- **Left set aside (2):** bug-36 (f228-03 removes it, its work done by F228) and bug-60 (stopping a looping local attempt: F195's thread decides it, after finding why the local model fails).
- **Removed by f231-01 (47, and f9-12):** bug-05, bug-08 to bug-35, bug-37 to bug-47, bug-50, bug-52, bug-53, bug-55, bug-58, bug-61, bug-62; f9-12 too, which is what bug-44 asked. Why, in groups:
  - covered by a card on the board: bug-23 and bug-42 (F132), bug-28, bug-30 and bug-58 (F216, whose f216-02 rewrites `_to_html`), bug-44 (done here);
  - no longer bites: bug-05 (the runner runs from its `live` copy now, so a half-saved file in the repo can't break it), bug-12 (the clear-out ran long ago), bug-61 and bug-62 (leftovers of the week park F219 removed);
  - rare cases, never seen twice, or only the numbers: the rest. Their findings stay in the reviews in `.softfield/reviews/`, and git keeps every ticket.

## Decisions
- **D1. A request `drop_ticket`**, subject the ticket's id, applied by the runner as `drop_seed` is (`_drop_seed` in `runner/requests.py`): the file `git rm`ed from `.softfield/tasks/later/` in a commit of its own, "<id> removed by the owner", its row marked `removed`. Refused, main unchanged, for an empty subject or a ticket not in `.softfield/tasks/later/` (ready, running, blocked or done): "<id> is not set aside: not removed". A blocked ticket is set aside first, then removed.
- **D2. No new owner command.** The dashboard asks; `softfield queue` stays the only terminal twin.
- **D3. The ticket page** gets Remove beside Queue it, folded behind one more press as Remove seed is, then the dashed "Removing · on its way" plate at once (mock-up: `.softfield/cards/f231-mockup/remove-a-set-aside-ticket.html`).
- **D4. The board's seed card** shows a waiting Remove or Queue it with the dashed edge and a "removing" or "queuing · on its way" line, as a reorder does.
- **D5. The clean-up is a plain `rm`** in a lead ticket (f231-01), as f228-03 removes bug-36: it needs nothing new and can run first.

## Tickets
| # | id | who | depends on | what |
|---|----|-----|------------|------|
| 01 | clear-the-seed-row | lead | – | D5: removes the 48 tickets listed above |
| 02 | drop-a-set-aside-ticket | lead | – | D1, D2: the runner's request |
| 03 | remove-on-the-ticket-page | developer | 02 | D3 |
| 04 | seed-card-on-its-way | developer | 02 | D4 |

## Before and after
- `/tickets/bug-60-stop-repeated-failed-calls`
- `/board`
