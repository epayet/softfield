---
id: f15-09-fix-populates-waits-for-cards
milestone: f15-reprioritising-tickets
difficulty: 3
depends_on: []
files:
- factory_dashboard/board.py
tests:
- tests/factory_dashboard/test_board.py
finding: f68-i-want-the-factory-to-be-C1080-1
---

### Goal
Fix a checkpoint finding on f15-08-card-says-what-it-waits-for: Populates waits for cards outside planted and growing stages

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f15-08-card-says-what-it-waits-for.md`. What it found is under Finding:
- f68-i-want-the-factory-to-be-C1080-1, should-fix: in `factory_dashboard/board.py`, line 294.

### Finding
f68-i-want-the-factory-to-be-C1080-1: Populates waits for cards outside planted and growing stages
> The code calls `_card_waits` for every milestone, so seed, sprouting, ripe, and harvested cards can expose nonempty `Card.waits` even though only planted and growing cards wait. This breaks the Goal: “A card on the board whose tickets can't start yet says which cards it waits for.” Restrict the field to the eligible stages, not just the note displayed on the page.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 9569
gate_failures: ['all-tests', 'stopped']
tokens: 2484242
```
