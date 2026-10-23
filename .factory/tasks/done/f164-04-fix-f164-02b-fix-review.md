---
id: f164-04-fix-f164-02b-fix-review
milestone: f164-i-like-reading-the-milestone-reviews
difficulty: 3
depends_on: []
files:
- factory_dashboard/milestones.py
tests:
- tests/factory_dashboard/test_milestones.py
finding: f51-when-a-plan-depends-on-an-C1366-1
---

### Goal
Fix a checkpoint finding on f164-02b-fix-review-ideas-lookup: Plant requests are not matched independently for every idea

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f164-02b-fix-review-ideas-lookup.md`. What it found is under Finding:
- f51-when-a-plan-depends-on-an-C1366-1, should-fix: in `factory_dashboard/milestones.py`, line 638.

### Finding
f51-when-a-plan-depends-on-an-C1366-1: Plant requests are not matched independently for every idea
> This breaks the Done when: “two ideas of one review, each with its own plant request in the same project, each show their own state”. The code chooses one target project for the whole review, so a mixed Product/Factory sheet ignores Product requests stored in the review project. Also, when an idea has no `from` field, the fallback selects the newest request from that project before checking its text; that can mask an older request matching another idea.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 943
gate_failures: []
tokens: 563238
```
