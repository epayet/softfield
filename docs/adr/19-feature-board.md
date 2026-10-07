# ADR 19: A board of milestones and bugs, planner questions, and priorities that the runner follows

- **Status:** Accepted (by the owner, 2026-10-02)
- **Date:** 2026-10-02
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 13](13-factory-dashboard.md) (new pages); `docs/task-format.md` (a `feature:` field); `runner/tasks.py` `pick_next` (priority before milestone order)
- **Evidence:** the owner's notes after F2 (`docs/roadmap.md`, "Owner's notes after F2", "The feature board"). The owner chose files in the repo over Linear (2026-10-02).

## Context
- **The owner has more ideas than Claude's window can discuss.** They want to:
  - keep a list of features and bugs, each with a state;
  - add and search features, and see the done ones;
  - reorder them and have the workers follow;
  - plan them with the lead whenever it has room.
- **Today ideas live as roadmap sections, bugs in `docs/backlog.md`, and the queue is milestone order then ticket number** (`pick_next`). Nothing ranks a bug against a feature.

## Decisions (draft)
1. **A card is a milestone, from the idea stage** (one thing, not two).
   - Adding an idea creates `docs/milestones/<key>.md` at once, with the next free key in its series, the owner's notes and two header lines: `State:` and `Priority:`.
   - States: idea → planning → ready → building → needs sign-off → done.
   - A milestone is planned from its own card. There is no separate feature file, and the roadmap's ideas move into cards over time.
2. **⚑ Bugs are tickets outside milestones, and first-class cards** (owner, 2026-10-02; amends `docs/task-format.md`).
   - A bug is `bug-<nn>-<slug>` with `milestone: bugs`: no plan or sign-off, done when it merges. Checkpoints read it like any merge.
   - On the board each bug is its own card in the same field, with its own states:
     - **seed:** its ticket is in `tasks/later/`;
     - **ready:** its ticket is in `tasks/ready/`;
     - **growing:** a job is running on it;
     - **harvested:** merged.
   - `docs/backlog.md` becomes bug tickets in `tasks/later/` over time, with the lead triaging.
2b. **Area: factory or product** (owner, 2026-10-02). Every card says which, like an epic: a milestone doc's `**Area:**` (default from its series: `f` factory, `m` product), and a bug ticket's `area:`. When the factory is extracted to control several projects (ADR 02), the area becomes the project; sub-areas wait for a real need.
3. **⚑ Priorities** (amends `runner/tasks.py` `pick_next`): a card's `Priority:` and a bug ticket's `priority:` (an integer, lower first).
   - The runner picks by priority, then milestone order, then ticket number. A change takes effect at the next pick.
   - The lead sets priorities at planning; the owner changes them, on the console or the board (owner, 2026-10-02).
4. **The board:** `/board` on the dashboard.
   - Columns by state; the cards are milestones and bugs, coloured by area, with bugs marked as bugs; search; the harvested column shows the latest few, with a link to the rest.
   - A card opens its milestone page, which gains the notes and the planner answers.
   - **Read-only at first** (owner, 2026-10-02): cards are created, edited and reprioritised in a Claude Code session. Moving, editing and adding cards from the board come later, as [ADR 18](18-dashboard-writes.md) requests, with the planner questions.
     - Reprioritising from the dashboard is now an ADR 18 request, as item 3 foresaw ("the owner changes them, on the console or the board"): `priority` (F6 D1, f6-18), from the ↑ and ↓ of Next in line's tickets and of the Milestones page's cards.
   - **A mock-up comes before its tickets** (lead.md).
5. **Planner questions** (asynchronous; later, after the read-only board):
   - On a card, the owner writes a question or a thought at any time, even while Claude is at its limit.
   - Each becomes a `planner` lead job at the highest priority. It answers in the card's doc when Claude has room, and proposes the next step (an ADR draft, tickets, "ready to plan").
   - It counts in the owner's 25% of Claude's window: it's the owner's own work.
6. **The Overview stays the factory floor** (F3); the board is its own page.

A live chat and Claude suggesting features are in the roadmap, not here (owner, 2026-10-02).

## Open questions
None left (2026-10-02).
