---
id: f283-01-find-lights-up
milestone: f283-the-current-planning-search-reloads-the
difficulty: 3
depends_on: [f123-01-shared-order-script]
files:
  - factory_dashboard/static/board.js
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
Typing in the board's box lights up the cards that match and fades the others, each in its place, without a reload, so the owner can drag a found card next to the ones around it.

### Context
Read D1 to D4 in `.softfield/cards/f283-the-current-planning-search-reloads-the.md`. The picture to build is `.softfield/cards/f283-mockup/board-highlight.html`, its Proposed (wide), apart from "N lit", Next › and the plots' tags, which are f283-02's.
- `factory_dashboard/templates/board.html`, the `board-filter` form: the label reads "Find"; the button Enter sends today becomes "Show only these" and keeps sending `?q=` with the kind. Without the script the form works as today.
- `factory_dashboard/static/board.js`: on `input` and on Enter, read the key and title each `.slot` shows and toggle `lit` on the slot and a class on `#field` while the box holds text (D2's matching rule, done in the browser); Enter is kept from submitting while the script runs; Esc and the box's × clear it. Mark the matching words of a lit card's title with `<mark>`, from the title's text, never by writing the box's text as HTML. After `refresh` swaps `.stages`, light the new cards again.
- `factory_dashboard/static/dashboard.css`: add `--lit` to both `:root` blocks (D3's values) beside the other tokens, then the fading (follow `.dev-view .slot.dev-none` and its hover rule) and the lit edge, glow and tag. A dragged slot (`.dragging`) is never faded.
- `factory_dashboard/board.py` `_matches` stays as it is.
- Follow the browser tests in `tests/factory_dashboard/test_board.py` (the drag and refresh ones).

### Done when
- in the browser: typing "top bar" lights every card whose key or title holds both words, fades the rest, keeps every card where it was, and makes no request; the page's address doesn't change
- "f38" lights F38 and not F380 or a title with "f38" in it; "38" does the same; "bug-4" lights bug-40, bug-41 and bug-42
- Enter doesn't reload; "Show only these" loads `?q=` as today's Search does; Esc clears the light
- a faded card can still be dragged, and the light stays after the drag and after a 10 s refresh that swaps the cards
- a title holding `<b>` text shows it as text, with the match marked
- the listed `tests:` pass, and the new ones fail without the change
- all gates pass (see `docs/workflow.md`)
