---
id: f268-03-add-a-picture-in-both-boxes
milestone: f268-having-the-ability-to-upload-files
agent: lead
difficulty: 5
depends_on: [f268-01-pictures-stored-with-the-request]
area: factory
files:
  - factory_dashboard/static/files.js
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/thread.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
The Plant box and a thread's reply box take up to 6 files of any kind, sent unchanged with the words.

### Context
The picture to build: `.softfield/cards/f268-mockup/pictures.html` (Proposed). Read ADR 49 item 1 and D1, D4 in `.softfield/cards/f268-having-the-ability-to-upload-files.md`. The boxes are the `#plant` form in `factory_dashboard/templates/planning.html` and the `#reply` form in `factory_dashboard/templates/thread.html`; each builds its value in `hx-vals`, which gains `files` from `files(form)`. Styles join `factory_dashboard/static/dashboard.css` from its existing tokens (the tray's stripe is `--stripe`, the frame `--shot-frame`, the chip's corner `--notch`). Follow the browser tests already in `tests/factory_dashboard/test_planning.py` for a phone and a wide screen; test files can be made in the test.

### Done when
- both boxes show "Add a file" (`multiple`, no `accept`); a picked, pasted or dropped file shows before sending: a picture as a thumbnail, any other file as a chip with its name and size, each with a ✕ that removes it
- a seventh file or one over 25 MB is refused in the box, at once, with a line saying which and why, and the others stay
- sending puts each file in the value's `files` as its name and a `data:` URL of its exact bytes (a test decodes it and compares); the box, previews included, empties after a send as the text does today; a send without files sends the value it sends today
- on a 390 px wide page the tray and the buttons fit without sideways scrolling
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
