---
id: f85-06-fix-unstyled-page-not-a-picture
milestone: f85-when-i-sign-off-a-task
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/shots.py
  - runner/milestone.py
tests:
  - tests/runner/test_shots.py
  - tests/runner/test_milestone.py
---

### Goal
A page whose stylesheet didn't load is recorded as a failed picture, with the stylesheet's address and why, instead of counting as taken.

### Context
Read D12 and "Unstyled and missing pictures" in `.softfield/cards/f85-when-i-sign-off-a-task.md`. Then `_browse` and its `draw` in `runner/shots.py`, and how `tests/runner/test_shots.py` serves its tiny test apps.
- In `draw`, before `page.goto`, note every request whose `resource_type` is `stylesheet` that fails (`requestfailed`, which includes those the guard aborts) or answers 400 or more. After the screenshot, the first one makes the picture `Picture(FAILED, "drawn without its stylesheet: <path> answered <code>")`, or `… <address> was refused` for one the guard aborted (another host). The path is the request's, without the origin.
- The `.png` stays in the folder: the dashboard shows only the reason for a failed picture (`factory_dashboard/milestones.py`, unchanged), and the file helps whoever fixes the project's `[shots]`.
- `review_pictures` in `runner/milestone.py` lists every `after-*.png` in the folder today. It must list only the after pictures the card's list file (shots.json, D5) records as taken, so a review never compares an unstyled page with the mock-up; with none taken it says "none", as now.
- Fonts, images and scripts that fail don't count: only stylesheets.

### Done when
- a test app whose page links `/static/app.css` that answers 404 gives `failed` pictures whose reason names `/static/app.css` and 404, and the `.png` files exist
- a page linking a stylesheet on another host gives `failed` with "was refused"
- a page whose stylesheet loads is `taken`, as before
- `review_pictures` leaves out an after picture recorded `failed` whose file exists, and says "none" when no after picture was taken
- the listed `tests:` pass, and fail without the change
- all gates pass (see `runner/instructions/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
