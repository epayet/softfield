# Review: F222, A newly approved plan goes last on the board

- **Status:** review round 1 done, waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- **The queue is one list.** The board's order now lives in `.softfield/order.txt`, one card or bug per line. Only the runner writes it: your drags, an approval, a queued bug. The runner picks the work from it, and the pages read the database's copy of it.
- **A plan you approve goes last.** When you approve the first plan of a seed or a card being planned, the card goes to the very end of Planted, behind the newest card, in the same commit as the approval. A bug you queue from Set aside goes to the end too. A replan, a second plan, a plan with no ticket, and Try again on a blocked ticket leave the order as it was. Approve first (F224) still puts the card first.
- **The priority number is gone.** On the Overview, Next in line says the ticket's card (`F208`) or `bug` where it said "priority N". A card's page says **Place: #1 in Planted** while the card is a seed, sprouting or planted. A ticket waiting in ready says "In line with F169, #1 in Planted". The Priority columns left Milestones and Set aside, and a set-aside ticket now says "Queued, it goes to the end of the line". The ↑ ↓ priority request is gone; one still waiting is answered "move it on the board".
- **Today's order was kept.** The runner wrote the list once from the old numbers, then took the number out of every open card and bug in one commit (`aa4d06fc`). `softfield run --dry-run` says "place N", and a planner's "Where the work stands" lists the cards in queue order.
- Nothing changes for Mum: this is the factory only.

The after pictures match the mock-up where the sample data shows it: Next in line says `F208` and `F71`, and no Priority column or "priority N" is on any page. The sample's ticket pages and card page are of finished work (bug-07, f169-01, F169 harvested), so the new "Place" and "In line with…" lines don't show in them. F222's own page shows "Place: #1 in Planted". The before pictures all failed with a 500: the old code can't read the database once the `milestones.priority` column is dropped (see What next, Factory).

### 2. How to test it yourself
1. On the board, note the order of Planted. Approve a plan on a seed that has tickets. After the runner's next pick, it should be the last card of Planted, and the answer on its thread should end "goes last on the board".
2. Approve a replan on a card already in line. It should stay where it was.
3. Drag two cards and press Send new order. After the next pick, the order should hold, and the runner's commit "the board's order, by the owner" should change only `.softfield/order.txt`.
4. On Tickets → Set aside, queue a bug. It should go to the end of the board.
5. On a phone, look for any priority number on the Overview's Next in line, Tickets, a set-aside ticket, Milestones and a planted card's page. There should be none. The planted card's page should say "Place: #N in Planted".

### 3. Left for later
Nothing set aside as a ticket. One nit is noted in Findings (F3): done cards still have their old number, and nothing reads it.

### 4. Decisions waiting for you
None. [ADR 45](../adr/45-one-queue-order-no-priority.md) was accepted before the build.

### 5. How the work went
- 2026-11-05: the planner (Opus) planned the card in three jobs ($8.78), and drew the mock-up and ADR 45.
- 2026-11-12: f222-02 (the list, the move, the table) built by the lead on Opus in 19 minutes ($3.56). f222-01 (goes last) built on Sonnet in 27 minutes ($0.82). Both passed the first time.
- 2026-11-17: f222-03 (the pages) built on Opus in 29 minutes ($4.28). f222-04 (the number goes) built on Opus in 48 minutes ($12.71). Both passed the first time.
- 2026-11-17: review round 1 (Opus) added one missing test and tidied two templates.
- Lessons:
  - Splitting the change in two (D9: first the list writes the numbers too, then the numbers go) kept main right after every ticket, and the move ran on main with no hand edits. It is worth repeating for any field that gets retired.
  - The tests covered the cards being planned but not the seeds approved straight from idea. That is the case the owner hits most, and a review test now holds it.
  - Dropping a column broke the before pictures (every page answered 500 on the old code). The factory note below is about that.
- Logs: `.softfield/sessions/2026-11-05-0813.md`, `2026-11-12-1555.md`, `2026-11-12-1619.md`, `2026-11-17-0406.md`, `2026-11-17-1024.md`.

### 6. What next
- **Product:** product work is still on hold, as you asked.
- **Factory:**
  - The before pictures can't be taken once a milestone drops a database column, because the old code runs against the new database.
    > The before pictures should be taken on a copy of the database from before the milestone's first merge (or at plan approval), so a milestone that drops a column still gets its before pictures.
  - f222-04 cost $12.71, most of the card's build. A ticket that both removes a field everywhere and writes a one-off move is wide. The planner could split those two next time.

### 7. What clogged the factory line
From the `jobs` table:
- **Waiting for Claude's week pace: about 4.5 days.** f222-01 merged at 16:46 on 11-12. f222-03 didn't start until 08:04 on 11-17. Between those times, no lead ticket started after 07:43 on 11-13: lead tickets wait over the week's pace line (ADR 44 item 6), and all four of F222's tickets were the lead's (`runner/` is protected). The line wasn't idle: Qwen ran 23 developer jobs, and planners and reviews ran on the reserve ($66). This was the allowance working as designed. To unclog it, you could put a card like this in the fast lane when you want it sooner.
- No failed attempts, no escalations, no stops for you.

<!-- runner report -->
<!-- /runner report -->

## What was built
- **f222-02-one-order-file** (`a8f57297e`): `runner/order.py` reads `.softfield/order.txt`. The pick's `_cards` takes places from it, with what the list doesn't name after all it names. A new table, `board_order` (migration V15), holds the dashboard's copy; `sync_cards` and every write keep it equal to the file. `move_to_list` writes the list once per project, on main, in the order the pick took the work. `_reorder` writes the list (and, until 04, the numbers too). `_commit_files` can now create a file and remove it again if the commit fails.
- **f222-01-approved-goes-last** (`e05f7cd53`): `_approve_plan` puts a card whose state was idea or planning, now ready with tickets and not a replan, last in the list (`_last`), in the approval's own commit. Queue on a bug in `later/` commits it last too. Try again on a blocked bug moves nothing.
- **f222-03-pages-read-the-order** (`36ab9f423`): `queries.board_places` and `place`. The board, Next in line, `run_order`, Set aside and Milestones sort by place. The card's page shows a Place line and a ready ticket shows "In line with…". The Priority columns and "priority N" are gone.
- **f222-04-the-number-goes** (`f40bfee27`): `Card.priority`, `Task.priority`, the `priority` request, `_numbers`, `ticket_priority` and `DEFAULT_PRIORITY`/`BUG_PRIORITY` are gone, and V16 drops `milestones.priority`. The move also takes the number out of open cards and bugs, only once it can do so cleanly (the card and the frontmatter still read the same after). Pre-flight refuses `priority:` on any feature ticket, and on a bug once its project has moved. The dispatch says "place N", the planner's block has no numbers, and the instructions were updated (task-format, lead, bootstrap, owner).

## Findings and resolutions
- **F1, should-fix, fixed by the review (claude).** No test covered a card approved straight from `idea`: removing `IDEA` from the entering check would have stayed green. `test_a_first_plans_approval_puts_its_card_last_in_the_one_commit` is now parametrised over `planning` and `idea`. f222-01 had no checkpoint, so this is marked missed against the build's own tests.
- **F2, nit, fixed by the review (claude).** Removing the Priority cells left `</td>      </tr>` in `milestones.html` and two cells on one line in `tickets.html`. Both are on their own lines again.
- **F3, nit, report only.** About 90 done cards still say `**Priority:** N` (D8 removes it from open ones only), and `order.txt` keeps a line for a card once it is signed off (f164 is place 0 today) until the next write prunes it. Both the pick and the pages place it the same way, so it orders nothing.

Checked and fine: a refused approval leaves the list as it was. The running bug keeps its line (`_open_bug`). The runner and the pages agree on unlisted keys. The move runs on main only and commits nothing the second time. `_card_unnumbered` refuses an edit that would change the card. No page or instruction still says a priority number, apart from `projects.priority`, which F123 and F193 keep on purpose. No French changed.

## Set aside
Nothing.

## Stop reason
None: one round, with everything fixed or noted.

## Factory
- **Flow:** four lead tickets, all passed on the first attempt. There were no checkpoint findings, no escalations, no stops and no input from you. The 4.5-day gap was the week's pace hold on lead tickets (see 7).
- **Models:** Opus planned ($8.78) and built three tickets ($20.55). Sonnet built the smallest runner ticket ($0.82), and it was as clean as Opus's.
- **What to change:** take the before pictures from a database snapshot taken before the milestone, so schema changes don't blank them (quoted in What next). Split a field's removal from its migration when the planner sizes a ticket.
