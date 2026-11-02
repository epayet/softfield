---
id: f123-02-projects-drag
milestone: f123-projects-page-drag-to-reorder
difficulty: 4
depends_on: [f123-01-shared-order-script, f123-01-projects-drag]
files:
  - factory_dashboard/templates/projects.html
  - factory_dashboard/static/projects.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
On the Projects page the owner reorders projects by dragging them, as on the board, and sends the new order once; the number boxes go.

### Context
Read `.softfield/cards/f123-projects-page-drag-to-reorder.md` (D1 to D6). The picture to build: `.softfield/cards/f123-mockup/projects-drag.html` (its Proposed).
- Use the shared script f123-01-shared-order-script adds in `factory_dashboard/static/` (`window.Order`, D5) for what is out of place, the moves, the ⋯ menu's moves, the drag and the send; don't copy any of it. `factory_dashboard/static/board.js` shows how a page calls it; `factory_dashboard/templates/board.html` shows `#order-bar`, `#order-sheet` and how the two scripts are loaded with `static(...)`. Don't change either.
- Today's page: `factory_dashboard/templates/projects.html` (`#projects-order`, its inline script) and `factory_dashboard/projects.py` (`order_on_its_way`, `projects_page`, which already sorts the projects as sent and passes `asked`). That Python file doesn't change.
- The request stays as it is: `kind=project_order`, `project`, and `value` the JSON list of every project's name in the order shown.
- `factory_dashboard/static/projects.js` is a new file holding only what is the Projects page's own: the rows, their places, the "moved · was #N · not sent yet" note, the bar's words ("N projects moved. Nothing is sent yet."), the on-its-way marks after a send.
- f123-01-projects-drag already gave each row (`li.proj`) its `data-key`, its place `#1`, `#2`… and the "on its way" marks when an order waits. The script gives each row its grip (`aria-label` "Drag <name>") and its ⋯ (`aria-label` "Move <name>"), as the board's script does for its cards, and keeps the places right while moving. The number inputs, the inline "Send new order" button, `#order-sent` and the inline script go.
- After a send the script shows every row on its way without a reload; dragging stays possible and a new send replaces it.
- The grip, ⋯, drag and drop-line CSS is already generic (f123-01). New CSS goes in the Projects page's block of `dashboard.css`, on the tokens; drop `.place input`, `.place input.asked`, `.send-order` and `.on-its-way` there once nothing uses them.
- Browser test examples: `test_dragging_a_card_by_its_grip_moves_it_and_back_again` and `test_send_posts_the_whole_open_order_once_and_the_board_shows_it_on_its_way` in `tests/factory_dashboard/test_board.py`.

### Done when
- dragging softfield's grip above travel-companion marks softfield "moved · was #2 · not sent yet" and shows the bar with "1 project moved. Nothing is sent yet."; dragging it back removes the mark and hides the bar
- the ⋯ menu's Top moves a project to #1 the same way
- Send posts one `project_order` whose value is every project's name in the order shown, and each project then reads "on its way · at the runner's next pick"
- with a `project_order` waiting, a project can still be dragged, and sending again posts a new `project_order`
- the page has no `input type="number"` any more
- `test_the_projects_page_lays_out_at_phone_and_display_sizes` still passes at both sizes, with the grip and ⋯ at least 44 px tall
- `test_send_lights_up_only_for_another_order_and_sends_the_names`, which relied on the number boxes, is replaced by the ones above
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
