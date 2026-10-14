---
id: f90-01-seed-shows-its-note
milestone: f90-editing-seeds-that-i-ve-planted
difficulty: 3
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A card's thread page shows the owner's whole note (its doc's `## Notes`) under the title, not only the title cut under 60 characters.

### Context
Read `.factory/cards/f90-editing-seeds-that-i-ve-planted.md` (Why it happens, D1, D2), then `thread_page`, `_header` and `_repo` in `factory_dashboard/planning.py` (`_adr_waits` is the example of reading a file from the checkout), and the `#card` header in `factory_dashboard/templates/thread.html`.
- The doc is `milestone_file(repo, "milestones", full_key(repo, thread))` (both in `runner/tasks.py`); its notes are the text between `## Notes` and the next `## ` line, stripped. "(none)", no section, no doc, no checkout, or the general thread: no note.
- Show it with `white-space: pre-line`, escaped like the messages are (no `| safe`).
- With no messages: in `<section id="note">` right under the header, plain. With messages: the same section as a `<details>` folded, summary "Your note", min-height 44px like the other summaries.
- Tests build the card's doc in the test project's repo folder; see how the existing thread tests set up `projects.repo`.

### Done when
- a seed whose doc's Notes are a 120-character note shows all of it in `#note`, while the title stays cut with "…"
- a card with a thread shows the note inside a folded `<details>` "Your note"
- a doc without `## Notes`, or with "(none)", and the general thread: no `#note`
- a project whose repo isn't a folder here: the page renders, no `#note`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
