---
id: f6-10-planning-phone
milestone: f6-planning-room
depends_on: [f6-07-thread-page, f6-08-proposal-review]
difficulty: 4
files:
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On a phone, the thread and the review show one point at a time as a big card with Comment…, ◀ ▶ between points, and the Send button pinned at the bottom.

### Context
Read the mock-up (`docs/milestones/planning-room-mockup/Main.dc.html`, `docs/milestones/planning-room-mockup/Review.dc.html`, `docs/milestones/planning-room-mockup/Phone.dc.html`: read the markup and the data in each script, not pages to open) (`docs/milestones/planning-room-mockup/Phone.dc.html`), `factory_dashboard/templates/thread.html` (f6-07), `factory_dashboard/templates/proposal.html` (f6-08) and the layout tests in `tests/factory_dashboard/test_planning.py`.
- **Under 640 px:**
  - the points become one card at a time, with a dot per point (marked where there's a comment), ◀ ▶ buttons and the textarea in the card;
  - Send stays at the bottom (`position: sticky`);
  - every tap target is at least 44 px.
- No script framework: plain CSS with radio inputs, or a few lines in the page, are fine.

### Done when
- at 390 px only one point is shown, ◀ ▶ change it, and Send is in view at the bottom (browser test)
- no horizontal scroll at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: all-tests)
attempts: 3
tokens: 4647917
logs: var/runs/20261007-005149/f6-10-planning-phone
```
