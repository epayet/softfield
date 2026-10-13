---
id: f109-03-merged-page-points-on
milestone: f109-when-plans-get-merged-i-need
difficulty: 4
depends_on: [f109-01-merge-links]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
From the thread page of any card merged away, the owner sees the plan it belongs to now: each card it was merged into, that card's open proposals and, once planned, its tickets, one tap away.

### Context
Read `docs/milestones/f109-when-plans-get-merged-i-need.md` (D7). f109-01 built the header's links: in `factory_dashboard/planning.py`, the function that reads a merged card's kept cards from the headings, and `thread_page`; in `factory_dashboard/templates/thread.html`, `a.merged-into` and the message form at the bottom (the dock). `_open_proposals` in the same file lists a thread's open proposals with their links.
- The owner (2026-10-13) wrote "Go" on F107's page, whose card was merged away: nothing could be planned there. The runner now sends such a message on to the kept card's thread (`_plan_message` in `runner/requests.py`), so no words are lost; this ticket makes the page say so before they write.
- **When:** the card has no doc on main and was merged into at least one card. A card on main again (F73 today) keeps its page as it is.
- The owner (2026-10-13): seeing the related plan from any merged card "is the main thing that was confusing me".
- **What shows:** a block `#merged-on`, with one part per kept card (`.merged-on-card`): "Merged into F95, <F95's title>: the conversation and its plans are there.", the link to `/planning/f95` (keep `{{ q }}`, at least 44 px tall); then one link per open proposal of that card's thread, by its title, to its review page; then, when that card has tickets (the `tickets` table, set-aside and removed ones left out), one link "Planned: 2 tickets, 1 done" to the card's page, `/milestones/<its full key>`. With neither, only the first link.
- **One kept card:** the block takes the place of the message form. **Several kept cards** (a number used twice before f109-02: F64, F73, F107): one part per card, most recent merge first, and the message form stays under them, since the runner can't tell which card a message is for.
- The thread's messages above stay readable. The Archive button stays.

### Done when
- with F107 merged into F95 and no F107 doc on main, `/planning/f107` has `#merged-on` with a link to `/planning/f95` and F95's title, and no message form (`textarea` for a message)
- an open plan on F95's thread is listed in `#merged-on` by its title, linking to its review page; an applied or rejected one is not
- a kept card with one ready and one done ticket shows "Planned: 2 tickets, 1 done" linking to its card's page; a kept card with no ticket shows no such link
- a key merged into two cards has two `.merged-on-card` parts, each with its own card's links, and keeps its message form
- a key that has a card on main again has no `#merged-on` and keeps its message form
- a card never merged, and the general thread, are unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
