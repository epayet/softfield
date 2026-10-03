---
id: f4-23-fix-the-checks-light-cannot
milestone: f4-always-on
difficulty: 4
depends_on: []
files:
- factory_dashboard/static/factory.js
tests:
- tests/factory_dashboard/test_line.py
finding: f4-always-on-C228-3
---

### Goal
Fix a checkpoint finding on f3-03-line-motion: The checks light cannot flash on the phone floor

### Context
A should-fix finding (f4-always-on-C228-3) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-03-line-motion.md`: in `factory_dashboard/static/factory.js`, line 351. What it found is under Finding.

### Finding
> The phone view draws its checks light inside `#floor-phone`, but this code always queries `#floor`. It therefore never adds a flash class to the visible phone light; the flash CSS is also scoped to `.floor`.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
