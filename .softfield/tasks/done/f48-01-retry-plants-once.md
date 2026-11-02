---
id: f48-01-retry-plants-once
milestone: f48-the-didnt-go-through-cards-try
difficulty: 5
depends_on: []
agent: lead
files:
  - runner/requests.py
  - runner/planner.py
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/thread.html
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
Try again on a note that didn't go through plants it once: a taken name never refuses it, and its old card leaves the desk as soon as the retry is sent.

### Context
Read `docs/milestones/f48-the-didnt-go-through-cards-try.md` (the Notes say what the database showed; D1, D2). In `runner/requests.py`: `_plant`, `refused`, `_WORKED`; in `runner/planner.py`: `card_named`, `slug`; in `factory_dashboard/planning.py`: `_refused`, `_again`; in `planning.html`: the `#plant` form and the desk's Try again; in `thread.html`: the `#reply` form.
- D1: a slug `card_named` finds taken is no refusal. If the taken card's doc holds the note's title and thoughts (whitespace collapsed), write nothing and return `planted already: docs/milestones/<stem>.md`; else the slug takes the first free `-2`, `-3`, … and plants as usual (with "Plant and ask the lead" too).
- D2: a hidden `again` in the Plant form and the reply form; Try again fills it (the reply form from the page's `again` query), a send clears it. The values carry it; the runner reads nothing from it. `_refused` leaves out a request whose id a later `plant`, `plan_message` or `send_back` value names as `again`, pending or done.

### Done when
- a plant whose slug a card has, with other words, plants `<key>-<slug>-2`; with the same words, its result is `planted already: …` and it isn't refused
- a refused plant named by a later plant's `again` leaves the desk while that plant is pending; if that plant is refused too, the desk shows only the new one
- the same for a refused message retried from its thread's reply box
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: blocked
reason: check-all failed; the work is on task/f48-01-retry-plants-once
```

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
note: its work from task/f48-01-retry-plants-once, landed in a terminal session on 2026-10-12 once check-all passed again
```
