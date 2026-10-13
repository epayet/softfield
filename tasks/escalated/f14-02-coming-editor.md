---
id: f14-02-coming-editor
milestone: f14-coming-planted-ideas-not-clickable
difficulty: 5
depends_on: [f14-01-change-request]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
  - factory_dashboard/overview.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A plant waiting in the desk's Coming group can be tapped to edit or cancel it, and the change shows at once wherever the plant shows.

### Context
Read `docs/milestones/f14-coming-planted-ideas-not-clickable.md` (Done when, D1 and D5), `coming` in `factory_dashboard/planning.py` (the plant rows: an open `owner_requests` row of kind `plant`), its rows in `factory_dashboard/templates/planning.html` (`#desk-coming`), and the plant form above them, which posts to `/requests` (the worked example in `factory_dashboard/requests.py`). `factory_dashboard/overview.py` lists the same open plants on the Now page.
- A change is a `change` request: `subject` the plant's request id, `value` `{"title", "thoughts"}` or `{"cancel": true}` (f14-01).
- A plant with an open `change` on it shows that change: the new title, or struck through with "cancelling at the runner's next pick"; both keep the dashed orange edge, and the row no longer opens.
- **Tapping a row opens it in place (no new page): the title and thoughts filled in, Save and Cancel it, each 44 px high for a phone.**

### Done when
- a waiting plant's row opens in place with its title and thoughts, Save and Cancel it
- Save posts a `change` with the new words; the row shows the new title at once, on its way, and no longer opens
- Cancel it posts a `change` with `{"cancel": true}`; the row shows struck through, "cancelling at the runner's next pick", and no longer opens
- the Now page's plant row shows the same change (new title, or struck through)
- a plant the runner has taken leaves Coming as today; a change that came too late shows its result ("too late: already planted") where the request's status shows
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 663229
logs: var/runs/20261013-174653/f14-02-coming-editor
```
