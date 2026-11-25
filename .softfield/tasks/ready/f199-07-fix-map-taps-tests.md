---
id: f199-07-fix-map-taps-tests
milestone: f199-let-s-improve-the-factory-floor
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_line.py
tests:
- tests/factory_dashboard/test_line.py
finding: f279-i-would-like-to-be-able-C2784-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f199-04-map-taps's tests: Map-card tests mostly assert source presence rather than behavior

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f199-04-map-taps.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f279-i-would-like-to-be-able-C2784-2, should-fix: in `tests/factory_dashboard/test_line.py`, line 3396.

### Finding
f279-i-would-like-to-be-able-C2784-2: Map-card tests mostly assert source presence rather than behavior
> The tests must check actual browser behavior and content, but several weak tests only inspect static HTML/JavaScript strings or merely confirm that some [data-what] element exists. Missing coverage includes station/seed/sprouting/planted/ripe/harvested/machine/belt card content and links, the Queue’s first ten crates and /tickets link, Enter and Escape behavior, refresh preservation with updated values, project_query on links, safe rendering of markup-containing titles, and phone target sizing. The planted test must open the card and verify all 57 cards in board order with milestone URLs; the belt test must verify label and today's count; machine tests must verify name/location/rating/work/link. The existing queue browser test is useful but covers only one station.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
