# ADR 19: A feature board, planner questions, and priorities that the runner follows

- **Status:** Proposed (draft, to discuss with the owner; items 4 and 5 especially)
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
1. **A feature is a file:** `docs/features/<slug>.md` with frontmatter:
   - `title`
   - `kind`: feature or bug
   - `state`: idea, planning, ready, building, needs sign-off, done
   - `priority`: an integer, lower first
   - `milestones`
   - `created`

   The body holds the owner's notes and the lead's answers. The backlog and the roadmap's ideas move there over time.
2. **Tickets name their feature** (`feature: <slug>`, optional). The runner picks by the feature's priority first, then milestone order, then ticket number. Reordering the board changes what runs next, at the next pick.
3. **The board:**
   - `/features` on the dashboard: a kanban by state, with search, and the done ones.
   - A feature's page lists its notes, ADRs, milestones and tickets. That's the pipeline in detail; the board is the high level.
   - Moving cards and adding features are [ADR 18](18-dashboard-writes.md) requests.
4. **Planner questions** (asynchronous):
   - On a feature's page, the owner writes a question or a thought at any time, even while Claude is at its limit.
   - Each becomes a `planner` lead job with the highest priority. It answers in the feature's file when Claude has room, and proposes the next step (an ADR draft, tickets, "ready to plan").
   - Accepting is the owner's, as today.
5. **A live chat on the web** (synchronous, a second Claude client): only if planner questions feel too slow. To discuss.
6. **Claude suggests features** with spare capacity: a lowest-priority lead job that adds features in the `idea` state for the owner to triage. Never above the owner's work.

## Open questions
- Who sets a priority: only the owner, or the lead at planning with the owner's veto?
- Does a planner question count against the 25% of Claude's window kept for the owner (ADR 16), since it is the owner's own work?
- How does this sit with milestones: is a milestone still the unit of sign-off, while features are the unit of priority?
- Is the factory line (F3) or the board the Overview?
