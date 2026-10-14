---
id: f15-01-reorder-request
milestone: f15-reprioritising-tickets
difficulty: 6
depends_on: []
agent: lead
files:
  - runner/requests.py
  - factory_dashboard/requests.py
  - docs/milestones/f5-board.md
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_requests.py
---

### Goal
The owner sends the board's whole order once, as a `reorder` request, and the runner makes the cards' priorities follow it in one commit at its next pick.

### Context
Read `docs/milestones/f15-reprioritising-tickets.md` (D3, D5) and F5's D1, D2 and D6 in `docs/milestones/f5-board.md`. In `runner/requests.py`: `_priority`, `_card_priority`, `_ticket_priority`, `_card_with`, `_commit_file`, `_COMMITS` and the dispatch that calls them. In `factory_dashboard/requests.py`: `KINDS`. In `runner/tasks.py`: `run_order` and `task_priority`. The tests to follow: the `priority` request's in `tests/runner/test_requests.py`.
- **The request:** kind `reorder`, no subject, value a JSON list of strings: the open cards' short keys (`f15`) and the open bug tickets' ids (`bug-07-queue-order`), first in line first. It is in `KINDS`, in `_COMMITS` (it waits for a clean main), and F5 D1's table gets its row.
- **What the runner does:** it sets each listed card's header `Priority:` and each listed bug ticket's `priority:` so that, by priority and then the key's own order (`run_order`), the listed ones come in the list's order. One commit, "the board's order, by the owner", holding only the files whose number changed. A card that keeps its place relative to its neighbours keeps its number when there is room; otherwise renumber.
- An open card or bug the list doesn't name comes after all the listed ones, in the order it had. A key that is unknown, done, removed or general is skipped and named in the result; it refuses nothing else.
- A ticket's own `priority:` inside a milestone is left as it is: it still wins over its card's (`task_priority`).
- A value that isn't a JSON list of strings, or holds a key twice, is finished with why, main unchanged.
- The result: `reordered: N cards changed` (and `, skipped F9, F12` when some were). The database's `milestones.priority` and the bug tickets' rows follow at once, as `_card_priority` does.
- A later `reorder` replaces an earlier one still open: only the latest open one is applied, the others are finished as `replaced by a later order`.
- **Protected work: test-first.**

### Done when
- with cards F7 (priority 100), F8 (100) and F9 (2) and the list `["f8", "f9", "f7"]`, the next pick takes F8's ticket before F9's and F9's before F7's; one commit by the runner holds it
- sending the order the cards already have changes no file and makes no commit
- a bug ticket in the list gets its `priority:`; a milestone ticket's own `priority:` is untouched
- an open card missing from the list sorts after the listed ones; a done card in the list is skipped and named in the result
- two open `reorder` requests: the later one is applied, the earlier finished as replaced
- a value that is not a list of strings, or names a key twice, is refused with why and commits nothing
- on a branch other than main the request stays open
- `POST /requests` takes kind `reorder` from the dashboard and still refuses an unknown kind
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
