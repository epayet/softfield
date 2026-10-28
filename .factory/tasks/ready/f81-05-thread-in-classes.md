---
id: f81-05-thread-in-classes
milestone: f81-assess-the-current-ui-state-of
agent: developer
difficulty: 4
depends_on: [f81-03-one-button-set]
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_proposal.py
---

### Goal
A card's thread and a proposal's review page are drawn from `dashboard.css` like the other pages: their sections are panels with plate headers, with no inline styles left but computed widths and positions.

### Context
Card doc `.factory/cards/f81-assess-the-current-ui-state-of.md` D6; the look is the Proposed side of `.factory/cards/f81-mockup/theme-pass.html` (`.panel`, `.btn`, `.desk-item`), applied to these two pages.
- `factory_dashboard/templates/thread.html` has about 81 `style=` attributes, `proposal.html` about 52. Move each into a class in `factory_dashboard/static/dashboard.css`, in a block headed by a comment naming the page; reuse `.panel`, `.btn`, the existing `#actions` and `.deck`/`.dock` rules and `.desk-item` (f81-04, if it is on main; else add it).
- An agent's or a status colour set per item from the template stays as a custom property (`style="--c: …"`), coloured by the class.
- Keep every id, `hx-*` attribute, `name`, script hook (`factory_dashboard/static/deck.js` reads `.deck`, `.deck-nav`, `.dock`, `.dock-host`) and word.
- Tests in `tests/factory_dashboard/test_thread.py` and `tests/factory_dashboard/test_proposal.py` that read an inline style read the class instead.

### Done when
- `thread.html` and `proposal.html` have no `style=` but computed widths, positions and `--c`
- a thread and a proposal show plate headers, in both themes, on a phone too, and the phone's one-point-at-a-time deck works as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
