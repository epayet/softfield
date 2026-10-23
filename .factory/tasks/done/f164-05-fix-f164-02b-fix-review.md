---
id: f164-05-fix-f164-02b-fix-review
milestone: f164-i-like-reading-the-milestone-reviews
difficulty: 3
depends_on: []
files:
- factory_dashboard/milestones.py
tests:
- tests/factory_dashboard/test_milestones.py
finding: f51-when-a-plan-depends-on-an-C1369-1
---

### Goal
Fix a checkpoint finding on f164-04-fix-f164-02b-fix-review: Id-less plant requests can still be matched to the wrong idea

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f164-04-fix-f164-02b-fix-review.md`. What it found is under Finding:
- f51-when-a-plan-depends-on-an-C1369-1, should-fix: in `factory_dashboard/milestones.py`, line 674.

### Finding
f51-when-a-plan-depends-on-an-C1369-1: Id-less plant requests can still be matched to the wrong idea
> This breaks the Done when: “what each finding describes no longer holds, and a test shows it”. For ideas without a `from` field, the fallback selects the first request for the target project (or project ID) before checking its text. Since requests are ordered newest first, that can select another idea’s newer request and leave an older matching request unnoticed. The existing same-project test uses `from` IDs, so it does not exercise this case.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1397
gate_failures: []
tokens: 942266
```
