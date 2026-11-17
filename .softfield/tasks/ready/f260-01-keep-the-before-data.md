---
id: f260-01-keep-the-before-data
milestone: f260-the-before-pictures-should-be-taken
agent: lead
difficulty: 5
depends_on: []
files:
  - runner/shots.py
  - runner/loop.py
  - runner/milestone.py
  - runner/owner.py
tests:
  - tests/runner/test_shots.py
  - tests/runner/test_loop.py
  - tests/runner/test_owner.py
---

### Goal
Keep a card's `prepare` data from just before its first ticket merges, and take a before picture that fails on today's data again on it, so a card that changes the schema still gets its befores.

### Context
Read "What happens today" and D1, D2, D4, D5 in `.softfield/cards/f260-the-before-pictures-should-be-taken.md`, and the amendment of 2026-11-17 in `.softfield/adr/40-pictures-at-sign-off-in-every-project.md`. Then `runner/shots.py` (`_round`, `_worktree`, `_pictures`, `_take`, `take`, `Picture`), the three `squash_merge` calls in `runner/loop.py` (`_merge` and the two others: the lead ticket's merge and the escalation's finish), the pictures line in `runner/milestone.py` built from `shots.read_list`, and `signoff` in `runner/owner.py`. Follow the tests in `tests/runner/test_shots.py` for a fake `prepare`, `serve` and browser. `runner/**` is protected: tests first.

The joints: the kept folder is `.softfield/var/shots/<key>/before-data/` with a file kept.txt holding the day (`YYYY-MM-DD`); a picture drawn on it records `"data": "<that day>"` in the card's shots.json (`LIST_FILE`) beside `state` and `reason`, which f260-02 reads. `_take` deletes only `*.png`, so the folder survives the rounds: keep it that way.

### Done when
- just before a card's first ticket squash-merges (no ticket of that card in `.softfield/tasks/done/`), with pages listed in its doc and `[shots]` set, `prepare` runs in a worktree of main before the merge into `before-data/`, and `kept.txt` says the day; a second ticket's merge, a card with no pages or a project with no `[shots]` keeps nothing
- a `prepare` that fails or runs out of time at the merge logs one line, leaves no `before-data/`, and the merge goes on
- at the review, a before that comes back `failed` on today's data is taken again on a throwaway copy of `before-data/`, in the same before worktree; when that one is taken, the list records it `taken` with `"data"`; the kept folder itself is unchanged after the round
- a before that is `taken` or `new` on today's data is not taken again, and has no `"data"`; with no `before-data/`, a failed before stays failed with today's reason
- the review's pictures line says, for a before with a `data` date, that it was drawn on the data of that day
- `signoff` removes `before-data/` and leaves the pictures and their list
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
