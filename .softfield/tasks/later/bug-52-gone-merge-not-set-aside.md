---
id: bug-52-gone-merge-not-set-aside
milestone: bugs
difficulty: 2
depends_on: []
agent: developer
area: factory
finding: f73-i-want-to-be-able-to-F3
files:
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
`_put_aside` skips a merge whose card has left main, as `_open_proposals` does.

### Context
From the old backlog file, in the review's words:

`_put_aside` (`factory_dashboard/planning.py`) counts a `merge` whose card has left main as open, where `_open_proposals` skips it with `_gone_merge`: a thread the owner archived whose only open proposal is such a merge shows under Set aside as "1 merge", with nothing left to decide. Fix: pass `_known_cards(repo)` and skip `_gone_merge` as `_open_proposals` does, with a test. Stays: needs a merge proposal left open and its thread archived by hand; not seen.

### Done when
- an archived thread whose only open proposal is such a merge isn't listed under Set aside
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)
