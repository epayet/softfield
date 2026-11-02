---
id: f73-01-set-aside-list
milestone: f73-i-want-to-be-able-to
difficulty: 4
depends_on: [f22-01-archive-at-the-bottom, f26-02-group-counts]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On the planning desk, what the owner set aside to come back to has a list of its own, "Set aside", apart from what is finished under "Archived".

### Context
Read `.softfield/cards/f73-i-want-to-be-able-to.md` (D1 to D3). In `factory_dashboard/planning.py`: `archived` (the list today) and `_open_proposals` (which proposals of a thread are still open; it skips archived threads). In `factory_dashboard/templates/planning.html`: the `<details id="archived">` block. Follow `test_the_archived_list_shows_the_most_recently_archived_first` in `tests/factory_dashboard/test_planning.py`.
- A thread is **set aside** when the owner archived it themselves (`planner_threads.archived_why` is `by you`) while its latest lead message that lists proposals still has one open: not applied, not approved, not rejected. `proposal_state` (imported at the top of that file) says which state a proposal is in; use it as `_open_proposals` does.
- Every other archived thread stays under Archived: approved, rejected, or archived by the owner with nothing open.
- A new function `set_aside(conn, project, now)` gives the list, most recently archived first; `archived` leaves those threads out, so no thread is in both.
- Each item's words: what waits in it, then when: `1 plan, 1 mock-up · set aside 3 days ago` (the kinds of its open proposals, counted; `ago` is imported at the top of that file).
- On the page: a `<details id="set-aside">` just above `<details id="archived">`, closed, titled `Set aside · N`, built like it; shown only when the list has items.
- The desk's groups, the Planning tab's count and Needs you don't change: a set-aside thread counts in none of them, as an archived one today.

### Done when
- a thread archived by the owner whose latest proposals hold an open plan is under `#set-aside` and not under `#archived`; its words say "1 plan" and "set aside"
- a thread archived as `approved`, and one archived by the owner with no open proposal, are under `#archived` and not under `#set-aside`
- a thread archived by the owner whose only proposal is applied or rejected is under `#archived`
- `Set aside · N` and `Archived · N` each count their own items; with nothing set aside there is no `#set-aside`
- the set-aside thread is in no group of the desk, and the Planning tab's count is the same with and without it
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 196786
logs: .softfield/var/runs/20261029-043403/f73-01-set-aside-list
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
