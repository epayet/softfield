# ADR 45: The queue's order is one list, and the priority number goes

- **Status:** Accepted (by the owner, 2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 19](19-feature-board.md) item 3 (a card's `Priority:` and a bug's `priority:`, "the lead sets priorities at planning"); `runner/instructions/task-format.md`; [F173](../cards/f173-dragging-a-card-on-the-board.md) D1, D2; [F15](../cards/f15-reprioritising-tickets.md) D5.
- **Evidence:** [F222](../cards/f222-when-milestones-plans-get-approved-do.md). F209's plan was approved after F215's and F216's, yet stands before both, because all three share the number 100 and a tie goes by card number.

## Context
- **The number is only a place, stored badly.** Since F173 a card's number means its place on the board and nothing else, but it lives in one file per card and bug. About 30 open cards share 100, so their order is really their card numbers.
- **A drag rewrites many files.** `_numbers` in `runner/requests.py` works out which numbers to change so the order holds, and a drag commits every changed doc.
- **The pages still say it:** "priority 5" on Next in line, "P5" on a card, a Priority column on Milestones and on Set aside. The owner has twice asked for it to go (2026-10-22 and 2026-11-05).

## The owner's decision (2026-11-05)
"Retire the priority system so that only queue order matters, it will be simpler this way. Then ensure that new tickets get appended to the end of the queue after planning is approved so that I know where to find them to reorder."

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ One list holds the order.** A project's `.softfield/order.txt` has one open card's short key or bug ticket's id per line, first in line first. Only the runner writes it. It replaces a card's `Priority:` and a bug's `priority:`.
2. **What the list doesn't name comes after what it names,** by card number, then ticket id. A new seed or a bug a review files needs no write. A line whose card is done or gone is ignored and dropped at the next write.
3. **⚑ What enters the line goes to the end.** Approving a card's first plan moves it to the end of the list, behind everything open, in the approval's commit. So does queueing a set-aside bug. A replan, a second plan, Try again on a blocked ticket and a sign-off move nothing.
4. **Each project moves over once, keeping its order.** The first time the runner finds no list, it writes one in today's order, in a commit, so nothing changes place.
5. **⚑ The number goes from the pages and the files.** Every page says a place or nothing. Open cards and bugs lose the field; pre-flight refuses `priority:` on any ticket. Docs of done cards keep their old line, and it is ignored.
6. **The dashboard reads a copy,** a database table the runner keeps equal to the list, as it does for every other card fact, so it never reads a branch's older list.
7. **A place is worked out, never stored on a card or ticket.** A card's page and a queued ticket's page show it from the list each time they open, so it can't go out of date (the owner, 2026-11-05: "when I browse a card I could see its number in the queue").

## What doesn't change
Dragging and one Send (F15); the fast lane (ADR 35), which goes first whatever the place; a waiting ticket's early place (F173 D6, D7); inside a card, `depends_on` then ticket id; a project's own order on the Projects page, which is a separate number the owner never sees.

## Cost and risk
- About four lead tickets, about $10 by my estimate: the average lead ticket has cost $1.37 since mid-October, and these are bigger, with about 280 test lines naming the field.
- **The risk is a queue in the wrong order** at the move. Item 4's test compares the list with the runner's order before it, and a card out of place is fixed with a drag.
- A plan branch's draft doc may still say `Priority:`. It is ignored.

## Alternatives turned down
- **Hide the words and keep the numbers in the files:** about half the cost, but ties, many-file drags and a field the lead can get wrong all stay, and the owner asked for the system to go.
- **A rank stored in each card or ticket:** this is today's system with unique numbers. Moving a card from the bottom to the top rewrites every card between, and each card that finishes shifts all those behind it, or leaves the stored numbers wrong. Of the last ten drags, one already changed 30 files and another 17, with shared numbers keeping that down.
- **The order only in the metrics database:** no file and no commit per drag, but three things get worse. The runner can run without the database and a failed write never stops it (`_record` in `runner/loop.py`), so a database problem would silently run work in the wrong order. A copy is made once a day, so a loss could take a day of drags. And the repo would no longer say what comes next, as it does for the cards and tickets themselves.
