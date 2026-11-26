---
id: f308-06-fix-note-box-on-a-phone
milestone: f308-when-an-adr-is-being-sent
agent: lead
area: factory
difficulty: 2
depends_on: []
files:
- factory_dashboard/static/dashboard.css
tests:
- tests/factory_dashboard/test_proposal.py
finding: f308-when-an-adr-is-being-sent-C19-1
---

### Goal
Fix a checkpoint finding on f308-04-fix-a-note-with-send: on a phone, the proposal's note box shows without its label and with 10 px text.

### Context
By the lead at a checkpoint, on the merge of `.softfield/tasks/done/f308-04-fix-a-note-with-send.md`. What it found is under Finding:
- f308-when-an-adr-is-being-sent-C19-1, should-fix: in `factory_dashboard/static/dashboard.css`, the phone rules at the end of the proposal dock's `@media` block (about line 960).

### Finding
f308-when-an-adr-is-being-sent-C19-1: on a phone the note box loses its label and is barely readable
> f308-04 made the note box show at 390 px, but its phone rules hide `.comment-box.change > span`, so the words "A note for the lead, on the whole proposal" are gone and the textarea has no visible or accessible name; they set the textarea to `font-size: 10px` (unreadable, and a phone browser zooms the page on focus under 16 px) and lean on four `!important`s. Card F308 D2 asks for the box labelled with those words, on the dock. `test_the_note_box_shows_on_a_phone` only checks that the textarea is visible and wider than 0, so it passed.

### Done when
- at 390 px on `/planning/f6/proposals/plan`, the words "A note for the lead, on the whole proposal" are visible above or beside the note box, the textarea's computed font size is at least 16 px, and the page has no `layout_problems` (`tests/layout.py`)
- the phone rules for the note box carry no `!important`
- the listed `tests:` pass, and fail without the change
- all gates pass
