---
id: f114-03-fix-notice-links-do-not
milestone: f114-i-want-to-be-notified-only
difficulty: 4
depends_on: []
files:
- factory_dashboard/overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f69-i-want-a-button-to-switch-C1035-3
---

### Goal
Fix a checkpoint finding on f114-01-notices-say-what-and-where: Notice links do not encode the project query value

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f114-01-notices-say-what-and-where.md`. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1035-3, should-fix: in `factory_dashboard/overview.py`, line 507.

### Finding
f69-i-want-a-button-to-switch-C1035-3: Notice links do not encode the project query value
> The notice URLs interpolate `project` directly, so a project name containing query delimiters such as `&` or `#` can be truncated or misparsed. This breaks the Done when: “every link keeps the page's project, as the other links of the partial do”. Encode the project value when building these links.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
