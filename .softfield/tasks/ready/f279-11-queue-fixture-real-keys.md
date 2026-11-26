---
id: f279-11-queue-fixture-real-keys
milestone: f279-i-would-like-to-be-able
difficulty: 2
depends_on: []
files:
  - tests/factory_dashboard/test_queue.py
tests:
  - tests/factory_dashboard/test_queue.py
finding: f279-i-would-like-to-be-able-F4
tests_only: true
---

### Goal
`/queue`'s tests store plan lines shaped like the runner's real ones, so a long milestone key in a job row is tested.

### Context
Read `LINES` in `tests/factory_dashboard/test_queue.py` and `_project_plan` in `runner/loop.py`, which writes the real lines.
- The runner names a checkpoint or a review by its milestone's full key, and its title is its reason: a real line is `PlanLine("softfield", "checkpoint", "f199-let-s-improve-the-factory-floor", "after f199-06-fix-map-taps and f199-07-fix-map-taps-tests merged", None, "jobs", None, "after f199-06-fix-map-taps and f199-07-fix-map-taps-tests merged", "f199")`.
- The fixture's checkpoint is `"f265"` with a short title, tidier than that.
- A real held job's waits reads "would park or go to a stand-in (claude: 5-hour window 89% used, over its cap of 75%)".

### Done when
- the fixture's checkpoint uses a full milestone key and the reason as its title, and a second job is a `review` held with the "would park or go to a stand-in (…)" waits
- the tests assert those rows' exact text: "<n> softfield checkpoint · <full key>", the card in capitals, and the held job's waits under "Waits for"
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass (see `docs/workflow.md`)
