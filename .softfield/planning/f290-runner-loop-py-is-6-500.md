# F290: Split runner/loop.py into one module per job kind, with no change in behaviour

The planning thread behind F290's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-24 08:26

> runner/loop.py is 6,500 lines and grows three lines for every one removed: plan splitting it by job kind (developer tickets, lead tickets, planner, reviews, waits) with no change in behaviour, one module per ticket.

## The lead, 2026-11-24 13:27

> I've drafted the split as eight lead tickets on `plan/f290`; the plan is in the card doc, and the eight tickets are in `.softfield/tasks/later/` and pass pre-flight.
>
> 1. **The plan: eight lead tickets, about $10 and three hours of the line**: loop.py is 6,813 lines today and its tests (test_loop.py) 9,342. The work follows F143, Split the planning room's code and tests by page. Its four move tickets each moved 1,400–3,400 lines for $0.55–$1.39 and took 10–19 minutes, using cp and sed. Here there are seven moves and one check, each waiting for the one before: the shared base, waits, a replan check, developer tickets, lead tickets, ratings, reviews, planner. All eight are the lead's because runner/ is protected. Other cards' developer tickets keep running beside them.
>    Action: Approve the plan; the eight tickets join the queue.
> 2. **A sixth piece you didn't list: what every job shares**: Your five kinds all use the same base: the Session, the clock, the job records, the queue's rows, routing and call_claude. That is about 1,500 lines with no single owner. If it stayed in loop.py, every new module would import loop and loop would import them back, which is the circle loop.py already works around with 18 imports inside functions. So it moves first, to runner/session.py, and the other modules import it. It is also the riskiest move, so it is better to find out early.
>    Action: Ticket f290-01, before the five you named.
> 3. **Ratings get their own module; ratings.py stays pure**: The code that reads and writes ratings in the database (about 380 lines) is not a job kind, and runner/ratings.py says at its top that it is pure maths. It goes to runner/rating_store.py, one module per ticket as you asked.
>    Action: Ticket f290-06.
> 4. **How "no change in behaviour" is held**: Tests move with their code, so the 9,342-line test file splits too. A test may change only its imports and the name it patches; its body and assertions stay as they are. Tests patch some names (now, call_claude, fresh_reading…) to control time and Claude. Moved code calls those through their module (session.now()), so one patch still reaches every caller. The real risk is that merging releases to live: a broken import on a rarely used path could stop the runner. mypy, already in the checks, catches imports placed inside functions, and the whole suite runs on every move.
>    Action: Decisions D2, D5 and D6 in the card doc.
> 5. **Splitting won't stop the growth**: The three lines added for each one removed come from new features, not from the file. After the split they will spread across seven modules. I recommend against a size check (you turn down gates that catch no real risk). Instead, one line in AGENTS.md: a new job kind gets its own runner/<kind>_job.py, and loop.py only schedules. The last ticket records each module's size, so the weekly review (F59, Periodic review of the factory) has a baseline to compare against.
>    Action: In f290-08; no gate.
> 6. **Where on the board: I recommend the top, right after F5**: 32 ready tickets name runner/loop.py. Each move rewrites the pointers it breaks in the ready and set-aside tickets in the same commit (as F143 did), or pre-flight would send those tickets back at their pick. At the end of the queue (143 tickets, about 6 days at 61 minutes each), more runner tickets get written against loop.py and each one reads the whole file. At the top, the work behind it (F124, F262, F279, F133…) reads modules of 500–1,800 lines. Drafts still waiting on other cards' plan branches aren't rewritten: pre-flight flags them when they're approved, and the planner fixes them then.
>    Action: After approving, drag F290 to just after F5 on the board and send. Or tell me here if it should wait behind something.
>
> Proposals:
> - Split runner/loop.py by job kind, move only (plan)
