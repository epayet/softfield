---
id: f164-06-fix-f164-05-test-tells-ideas-apart
milestone: f164-i-like-reading-the-milestone-reviews
difficulty: 2
agent: lead
depends_on: []
files:
- factory_dashboard/milestones.py
tests:
- tests/factory_dashboard/test_milestones.py
finding: f164-05-id-less-test-cannot-tell-ideas-apart
---

### Goal
Fix a checkpoint finding on f164-05-fix-f164-02b-fix-review: its test cannot tell a right match from a wrong one.

### Context
On the merge of `.factory/tasks/done/f164-05-fix-f164-02b-fix-review.md`, in `tests/factory_dashboard/test_milestones.py`, `test_id_less_idea_matches_by_text_not_project_fallback`.

### Finding
f164-05-id-less-test-cannot-tell-ideas-apart: the test asserts the same thing for both ideas
> Both requests are marked planted, with results `.factory/cards/f164-first.md` and `.factory/cards/f164-second.md`, and the test asserts `state == "planted"` and `card == "f164"` for both ideas. `card` is the milestone-like prefix of either file name, so the assertions hold whichever request each idea picked up. The old newest-first fallback would pass this test too.
> In `review_ideas`, the same whitespace and full-stop normalisation is written out three times (lines about 675, 689 and 709); an idea whose text is empty after normalising matches any request, since `startswith("")` is true.

### Done when
- the two ideas get different, asserted results (give the two requests different card ids, e.g. `f164` and `f170`, and assert each idea's own), and the test fails on the old fallback
- the normalising lives in one small helper used by all three places; an idea with empty text matches no request, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
