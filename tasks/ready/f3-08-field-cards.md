---
id: f3-08-field-cards
milestone: f5-board
depends_on: [f3-01-factory-line, f5-15-board-data]
difficulty: 3
files:
  - factory_dashboard/line.py
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The live line's five field stations (seeds, planting, rows, ripe, the stash) show the same counts as the board.

### Context
Read `docs/milestones/f3.md` D11 ("The field counts come from the board"), the docstring and the `Board` class of `factory_dashboard/board.py` (`board`, f5-15), and `live_line` in `factory_dashboard/line.py` (its `count` dict, near the end).
- Only the five field entries of `live_line`'s `count` dict change: seed → `seeds`, sprouting → `planting`, planted plus growing → `rows`, ripe → `ripe`, harvested → `stash`. The stash counts the harvested cards listed plus `more_harvested`: the board lists only the latest `HARVESTED`.
- `_field`, `_planting` and the document's `field` entry stay as they are: the drawing (`factory_dashboard/static/factory.js`) and the replay read their lists. Same document keys, so the drawing doesn't change.
- `factory_dashboard/board.py` imports from `factory_dashboard/line.py` at module level, so `line.py` imports `board` inside `live_line`, with a comment, as `factory_dashboard/overview.py` does for `line`.
- The board knows only the present: it is used when `live_line` is called without `at`. With a past `at` (the replay), the counts stay those of `field`.
- The `board_db` fixture in `tests/factory_dashboard/conftest.py` (`write_board`) already holds the cards the test needs; `document` in `tests/factory_dashboard/test_line.py` builds the line's document. The test goes in `tests/factory_dashboard/test_line.py`, not in a new file.
- Existing assertions on the stations' counts for these five stations change with the rule (for the board, a set-aside ticket of an ordinary milestone is no seed, and an idea no thread is about is a seed, not planting): compare them with the board. Assertions on `doc["field"]` don't change.
- Update the module docstring's "The field" line in `factory_dashboard/line.py` to say where the station counts come from.

### Done when
- for a fixture with two ideas, a set-aside bug, a sprouting card, a growing card and a harvested one, each field station's count in the live document equals the number of the board's cards for its stage, counted from `board`'s own result on the same database (no hard-coded number)
- with a past `at`, the five counts are those of the document's `field` (its `seeds`, `planting`, and the lengths of `rows`, `ripe` and `stash`)
- every existing assertion on `doc["field"]` still passes unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
