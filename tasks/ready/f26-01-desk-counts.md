---
id: f26-01-desk-counts
milestone: f26-i-want-to-see-numbers-next
difficulty: 2
depends_on: []
files:
- factory_dashboard/templates/planning.html
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
---

### Goal
Show how many items "Coming" and "Your desk" hold on `/planning`, in their headings.

### Context
Read `factory_dashboard/templates/planning.html` and `coming` and `desk` in `factory_dashboard/planning.py`.
- Worked example: the Archived heading in the same template, `Archived · {{ archived | length }}`.
- The desk's number is the sum of the items of its four groups: the same sum the Planning tab shows (`planning_count` in `factory_dashboard/app.py`).
- The Coming section is only rendered when it has items; keep it that way.
- The tests for both sections are under "Coming group (f6-20)" in `tests/factory_dashboard/test_planning.py`; reuse their helpers.
- The admin and the factory dashboard are English only: no translation needed.

### Done when
- with two Coming items, the Coming heading reads "Coming · 2"
- with items in several desk groups, the desk heading reads "Your desk · N", N being their total and equal to the Planning tab's number on the same page
- with an empty desk, the heading reads "Your desk" with no number and "Nothing waits for you." still shows
- the groups' own headings ("Your answers wanted", …) get no number
- the tests assert the exact heading text, and would fail on main
- the listed `tests:` pass
- all gates pass
