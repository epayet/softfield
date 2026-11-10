# Milestone F222: A newly approved plan goes last on the board

> **State:** ready · **Priority:** 3 · **Area:** factory
> Planted by the owner on 2026-11-05.

## Notes
When milestones plans get approved, do they get added to the back of the queue consistently? I sometimes struggle to find them again, it'll be easier if they get at the end and I can reshuffle manually if that's not the case atm

**The owner, 2026-11-05:** "Retire the priority system so that only queue order matters, it will be simpler this way. Then ensure that new tickets get appended to the end of the queue after planning is approved so that I know where to find them to reorder."

## What happens today (read from the code, 2026-11-05)
- Approving a plan changes the card's state and nothing else (`_approve_plan` in `runner/requests.py`): it keeps the Priority it had as an idea, 100 unless something changed it. The board sorts by Priority, then by card number.
- So a card lands last only if it has the highest number among the 100s. F209's plan was approved after F215's and F216's, yet F209 stands before both.
- Approving F133 today would put it in the middle of Planted, between F124 and F136.

## Outcome
- The queue is one list, and a place on it is the only thing that orders the work. No page and no open card says a priority number.
- A card whose first plan you approve goes to the very end of the list, and so does a bug you queue. You move them from there.
- Today's order doesn't change when the list is made.

**The picture:** [`f222-mockup/no-priority.html`](f222-mockup/no-priority.html).

## Decisions
[ADR 45](../adr/45-one-queue-order-no-priority.md) holds the rule; these are the joints.
- **D1: the list.** `.softfield/order.txt`, one key per line: a card's short key (`f222`) or a bug ticket's id. A new `runner/order.py` reads it (key to place, a missing file is empty) and writes it. Every sort keeps today's shape: place, then milestone order, then id, with what the list doesn't name after all it names.
- **D2: entering the line.** A card whose state was `idea` or `planning` and that the approval makes `ready`; a bug moved from `.softfield/tasks/later/` to ready by Queue. The write lists every open card and bug in their current order, then the one that entered, so it is strictly last, even behind a bug a review filed that the list didn't name. A place dragged earlier doesn't count: no exception to remember.
- **D3: what stays put.** A replan, a second plan, a plan with no ticket (F196, A planted card with no tickets, leaves that an idea), Try again on a blocked ticket, a merge, a sign-off.
- **D4: the move.** For every project, the first time the runner applies requests and finds no list, it writes the order `_reorder` starts from today (`was`), in one commit.
- **D5: the database copy.** A table `board_order` (project, key, place), rewritten by `sync_cards` and whenever the runner writes the list. A new `queries.board_places` gives the pages a key-to-place map, unlisted ones after, with the same sort as D1.
- **D6: the pages,** as the mock-up draws them. Next in line says the ticket's card or `bug` in place of "priority N". A card's page says "Place: #N in Planted", and only for a card in Seed, Sprouting or Planted. A ticket in ready says "In line with F169, #1 in Planted", or its own place if it's a bug. Both are worked out from the list when the page opens, never stored (the owner, 2026-11-05, wants to see the number while browsing). The Priority column leaves Milestones and Set aside. A set-aside ticket says "Queued, it goes to the end of the line; move it on the board once it is there."
- **D7: the words the lead reads.** `softfield run --dry-run` says "place N". A planner's "Where the work stands" lists cards in order without numbers.
- **D8: the number goes last.** Only once the runner and the pages read the list: `Card.priority`, `Task.priority`, the `priority` request, `_numbers`, the header and frontmatter lines of open cards and bugs (the runner removes them once per project, not by hand), the `milestones.priority` column, with pre-flight refusing `priority:` on any ticket. `projects.priority` stays: it is the Projects page's order (F123, F193).
- **D9: the order of the work.** The list comes first and writes both the list and the numbers, so main is right after each ticket.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 02 | one-order-file | lead | 6 | – | D1, D4, D5, D9: the list, the move, the table; the runner picks from it, and a drag writes it |
| 03 | pages-read-the-order | lead | 5 | 02 | D5, D6: the dashboard's order and the mock-up's words |
| 01 | approved-goes-last | lead | 3 | 02, f196-02 | D2, D3: entering the line goes to the end |
| 04 | the-number-goes | lead | 5 | 01, 03 | D7, D8: the field leaves code, docs, database and instructions |

All the lead's: `runner/` is protected, and 03 spans five pages. The numbers aren't in run order because 01 was drafted first.

## Before and after
- `/`
- `/tickets`
- `/tickets/bug-07-every-hx-target-is-on-its-page`
- `/tickets/f169-01-planner-searches-the-web`
- `/milestones`
- `/milestones/f169-why-is-web-search-related-tool`

## Done when
- Approve a plan on an older seed with tickets: on the board it is the last card of Planted, behind the newest card.
- Approve a replan on a card in line: it stays where it was.
- Drag two cards and press Send new order: the order holds, and the commit changes one file.
- No page shows a priority number: the Overview's Next in line, Tickets, a set-aside ticket, Milestones, a card's page.
- The board's order the day after the move is the order it had before it.
