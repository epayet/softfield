---
id: f109-03-merged-page-points-on
milestone: f109-when-plans-get-merged-i-need
difficulty: 3
depends_on: [f109-01-merge-links]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
The thread page of a card merged away says where the conversation and its plans are, with the kept card's open proposals one tap away, in place of a box to write in.

### Context
Read `docs/milestones/f109-when-plans-get-merged-i-need.md` (D7). f109-01 built the header's links: in `factory_dashboard/planning.py`, the function that reads a merged card's kept cards from the headings, and `thread_page`; in `factory_dashboard/templates/thread.html`, `a.merged-into` and the message form at the bottom (the dock). `_open_proposals` in the same file lists a thread's open proposals with their links.
- The owner (2026-10-13) wrote "Go" on F107's page, whose card was merged away: nothing could be planned there. The runner now sends such a message on to the kept card's thread (`_plan_message` in `runner/requests.py`), so no words are lost; this ticket makes the page say so before they write.
- **When:** the card has no doc on main and was merged into exactly one card. With two kept cards (a number used twice before f109-02) or a card on main again, the page stays as it is.
- **What shows in place of the message form:** a block `#merged-on` reading "Merged into F95, <F95's title>: the conversation and its plans are there.", the link to `/planning/f95` (keep `{{ q }}`, at least 44 px tall), then one link per open proposal of the kept card's thread, by its title, to its review page. With no open proposal, only the first link.
- The thread's messages above stay readable. The Archive button stays.

### Done when
- with F107 merged into F95 and no F107 doc on main, `/planning/f107` has `#merged-on` with a link to `/planning/f95` and F95's title, and no message form (`textarea` for a message)
- an open plan on F95's thread is listed in `#merged-on` by its title, linking to its review page; an applied or rejected one is not
- a key merged into two cards keeps its message form and has no `#merged-on`; so does a key that has a card on main again
- a card never merged, and the general thread, are unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
