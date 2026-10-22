---
id: f171-04-plant-takes-the-projects-area
milestone: f171-there-are-dupliacted-tickets-on-the
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/planner.py
  - runner/requests.py
  - .factory/project.toml
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
---

### Goal
A note planted without an area takes its project's area, so a product project's new cards are product cards with `m` keys instead of factory cards with `f` keys.

### Context
Read D5 in `.factory/cards/f171-there-are-dupliacted-tickets-on-the.md`, then `_area`, `planting`, `seed_area`, `SERIES` and `next_key` in `runner/planner.py`, and `_plant` in `runner/requests.py`, which has the repo.
- Today `_area` returns factory whenever a plant carries no area, and the Plant box's one-box note never carries one: travel-companion's cards went M1, then F1…F9, product work included.
- The project's area is `area` under `[project]` in the project's `.factory/project.toml`, `factory` or `product`; missing or unreadable, it is `product`. Add `area = "factory"` to softfield's `.factory/project.toml`, with a one-line comment.
- An area given in the request still wins. Keys already given are not renamed.

### Done when
- a one-box note planted in a project whose `project.toml` has no `area` is a product card with the next `m` key
- the same note in a project with `area = "factory"` is a factory card with the next `f` key, as softfield's are today
- a plant that gives an area keeps it, whatever the project's
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
