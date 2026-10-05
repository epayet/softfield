---
id: f9-07-fix-the-null-title-test
milestone: f9-line-polish
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_line.py
tests:
- tests/factory_dashboard/test_line.py
finding: f9-line-polish-C420-2
---

### Goal
Fix a checkpoint finding on f3-28-floor-words: The null-title test does not assert the row contains only its key.

### Context
A should-fix finding (f9-line-polish-C420-2) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-28-floor-words.md`: in `tests/factory_dashboard/test_line.py`, line 985. What it found is under Finding.

### Finding
> The assertions that the text starts with F1 and lacks the separator still allow extra text after the key, so a row that does not say the key alone could pass. Assert the exact expected text to check the requested content.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
