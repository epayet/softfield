---
id: f106-02-blocked-on-the-desk
milestone: f106-where-do-blocked-tickets-go-for
difficulty: 4
depends_on: [f12-03-remove-review-probe, f95-01-sign-offs-counted-once]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The owner's desk has a group "Blocked tickets" listing each blocked ticket with its reason, and the Overview's Needs you counts them through the desk only.

### Context
Read `desk`, `_refused` and `DeskItem` in `factory_dashboard/planning.py`, and `needs_you` and the lines building "needs" under it in `factory_dashboard/overview.py`. The example to follow: `test_a_refused_plant_waits_first_on_the_desk_with_its_words_and_counts` in `tests/factory_dashboard/test_planning.py`.
- A blocked ticket is an open row of `owner_items` (`resolved IS NULL`) with `kind = 'blocked'`: `subject` is the ticket's id, `text` is "<id> blocked: <reason>". Tests write one with `metrics.upsert_owner_item(conn, project_id, "blocked", "<id>", text=..., created=...)`, which returns the row's id, and resolve it with `metrics.resolve_owner_item(conn, item_id, at)`.
- D1 (`.factory/cards/f106-where-do-blocked-tickets-go-for.md`): `desk` returns a sixth group, key "blocked", name "Blocked tickets", colour "--hazard", second, right after "Didn't go through". One plain DeskItem per open row, oldest first: its title is the ticket's id, its words the row's text without the leading "<id> blocked: ", its link "/tickets/<id>".
- The Overview: f95-01 left the stored `signoff` rows out of Needs you because the desk's entry counts them. Do the same for `blocked` rows. The Planning tab's count and the desk entry's number follow from `waiting_for_you`, which counts every group.
- The existing test `test_other_kinds_still_show_with_their_command` in `tests/factory_dashboard/test_overview.py` asserts a `blocked` row's command shows in Needs you: change it to assert it doesn't, and keep its `adr` assertion.
- **Change no template: the desk's page already draws any group's plain items.**

### Done when
- two open `blocked` rows: the desk's second group is "Blocked tickets" with two items, oldest first, each titled with its own ticket's id and worded with its own reason (no item carries the other's), each linking to its ticket's page
- a resolved `blocked` row is not on the desk
- no open `blocked` row: the group is empty and `/planning` doesn't show its heading
- the Planning tab's count and the desk heading's count include the blocked tickets
- the Overview's Needs you has no row of kind `blocked` of its own; its desk entry's number counts them; rows of other kinds (`adr`, `reserve`) show as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
