---
id: f9-33-phone-belts-keep-words
milestone: f9-line-polish
depends_on: []
difficulty: 3
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
finding: f9-32-fix-phone-belt-words
priority: 40
area: factory
---

### Goal
On the phone, `queue→developers` reads "developer · N today", `lead→checks` reads "lead's work · N today" and `checks→lead` reads "back to the lead · N today", each where its words fit; every other phone belt reads as it does on main.

### Context
Read `belt`, `PHONE_BELTS` and `drawPhone` in `factory_dashboard/static/factory.js`, and `test_no_phone_label_overlaps_another_or_leaves_its_station` in `tests/factory_dashboard/test_line.py`.
- f9-22 added " today" to every belt's words, which made each about 40 units wider. That is why it added `short: true`: the longer words no longer fit where the labels were. So the `short` flags can't simply go back to their pre-f9-22 values.
- Sizes on the phone floor: it is 358 units wide, a belt label is about 6.6 units a character and 14 units high (about 10.5 above its `at` y, 3.5 below). A label with no `end` or `middle` starts at its `at` x and runs right.
- `queue→lead`, `checks→developers` and `merged→reviewers` keep `short: true` in this ticket. Their words come from the document ("lead tickets", "failed: retry", "checkpoints"); with " today" the first two leave the floor and the third runs over "CHECKS".
- `queue→developers` at `[262, 540]`: "developer · 1 today" is about 125 wide, so it ends near 387, off the floor. It fits under the belt's run at y 782, right of its drop at x 183 and above the reviewers (y 812): `at` `[196, 804]`.
- `lead→checks` at `[30, 1262]`: "lead's work · 1 today" is about 139 wide, so it ends near 169, over the checks station (x 134 to 224, y 1196 to 1306). It fits under the checks station and above Merged (y 1336), left of the `checks→merged` belt (x 179): `at` `[14, 1322]`.
- `checks→lead` stays at `[30, 1212]`; only its `short` goes.
- The label test is the judge of a position. Run it alone after each move: `uv run pytest tests/factory_dashboard/test_line.py -k "phone_label or phone_belts"`. If a label still overlaps, move its `at` a few units inside the band named above; don't change the test, the station sizes or the words.

### Done when
- on the phone, `queue→developers`, `lead→checks` and `checks→lead` read their `say` word, " · N today"; `seeds→planting` still reads "N today"
- in `PHONE_BELTS`, `short` is on `seeds→planting`, `queue→lead`, `checks→developers` and `merged→reviewers` only; only the `at` of `queue→developers` and `lead→checks` moved
- a test checks the three belts' text from the document's count, and `test_no_phone_label_overlaps_another_or_leaves_its_station` passes unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
