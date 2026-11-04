# ADR 43: The owner plants a review's small fixes

- **Status:** Accepted (by the owner, 2026-11-04)
- **Date:** 2026-11-04
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 35](35-no-backlog-file.md) items 1 and 6, and `docs/workflow.md`, "Milestone review loop" and "Discoveries".
- **Evidence:** F149 (owner, 2026-11-04): "rather than becoming a seed on my board, i imagined more of a 'plant this seed' option from the review". 52 bug tickets are set aside on Softfield's board, and the last 8 reviews added 5 of them with nobody asking.

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ A review writes no set-aside bug ticket.** A nit, or a should-fix point about untouched code, that is worth a run keeps the route `later`, but it becomes one quoted `> ` line in the sign-off sheet's "6. What next": one sentence naming the file, the problem and the fix. F164's plate shows it with Plant and Plant and ask the lead (F164 D1–D5). This replaces ADR 35 item 1.
2. **Under the bullet of the board it belongs on.** A fix to a project's own code goes under Product, unless the project is the factory, where it goes under Factory: F164 D2 sends a Factory line to Softfield's board from any project.
3. **Nothing about the fix is lost if it isn't planted.** The finding stays in the report and the metrics database, as a `report` one does. Nothing reminds the owner of it.
4. **⚑ Discoveries are triaged the same way:** a quoted line, a ticket or an ADR, not a bug seed. This replaces ADR 35 item 6's "bug seeds".
5. **What still goes without asking:** a blocking finding, a should-fix point on the milestone's own work, and any security finding take the routes `local`, `claude` or `adr` as today. A security finding is never only a line to plant.
6. **It starts when the buttons exist.** Until f164-03 is on main a quoted line has no button, so the prompt changes only after it.

## Alternatives turned down
- **Plant makes the bug ticket:** the review would write each ticket hidden, paid for whether or not it is planted, and Plant would need a new request kind. A plate's one sentence is enough for the lead to write the ticket when asked.
- **Keep seeds for should-fix points only:** two rules for one kind of finding, and three of the last five were should-fix.

## Consequences
- **Cost:** a set-aside ticket is ready to queue; a planted fix is an idea card, and Plant and ask the lead pays for a planner job to write its ticket (about $2.40 on average, 165 jobs since 2026-10-20). The review saves writing tickets nobody asked for.
- **Risk:** a real fix nobody plants stays only in its review. That is the owner's choice, press by press.
- The bug tickets already set aside stay on the board. The route's name and `ROUTES` (`runner/review.py`) don't change, so old findings still read.
