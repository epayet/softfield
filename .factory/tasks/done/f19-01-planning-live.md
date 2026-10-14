---
id: f19-01-planning-live
milestone: f19-will-i-need-to-refresh-planning
difficulty: 4
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
The Planning desk refreshes itself every 5 s, so a card moves to its new group without a reload, and a refresh never wipes what the owner is typing or closes what they opened to edit.

### Context
Follow the Overview's live wrappers in `factory_dashboard/templates/overview.html`: a `div` with `hx-get`, `hx-trigger="every 5s [window.liveIdle()]"`, `hx-select` and `hx-swap="innerHTML"`. Here the page polls itself (`/planning{{ q }}`) instead of `/live`.
- `factory_dashboard/templates/planning.html`: one wrapper around `#desk-coming` and one around `#desk` (not the `#plant` form, not `#tiles`).
  - Coming's wrapper goes inside the `{% if coming.items %}`, not around it: eight existing assertions use the bare string `desk-coming` to tell whether Coming is drawn, so it must not be on the page when nothing is coming. The `#desk` wrapper is always there.
  - In htmx, children inherit `hx-select` from a parent. Dismiss in `#desk`, and Save and Cancel it in `#desk-coming`, post to `/requests` and draw the answer in their own status `span`; with the wrapper's `hx-select` inherited they draw nothing. Each wrapper carries `hx-disinherit` naming `hx-select`.
  - `#desk-coming` and `#desk` are flex items of the row (`#plant-row` is `display: contents` in `factory_dashboard/static/dashboard.css`). Each wrapper has `display: contents` in its `style`, so the row lays out as before.
  - The page's own script already draws `#plant-row` and `#desk-coming` again after a plant, a Save or a Cancel it. Leave it as it is: htmx starts the poll on a wrapper it draws.
- `window.liveIdle` in `factory_dashboard/templates/base.html` waits on scroll and selection only. Make it also false:
  - while an `input` or `textarea` has focus;
  - while a `textarea` or a visible `input` holds text the owner typed: its text differs from what the page gave it (the field's default value). A waiting plant's editor arrives already filled, and hidden inputs carry values: neither counts;
  - while a `details` that holds an `input` or `textarea` is open (a waiting plant opened to edit).
- `factory_dashboard/templates/thread.html` is not part of this ticket: leave it untouched. The thread's poll is the lead's (the points' buttons are bound once at load by `factory_dashboard/static/deck.js`).
- Change no existing test. The browser tests open the page with `_open(page, serve())`; a waiting plant is `_finished(db_path, planning, "plant", None, DUCKS, None)`, as in `test_save_on_an_older_plant_posts_its_title_and_thoughts`.

### Done when
- `/planning`'s HTML has a poll around `#desk` with `hx-get="/planning?project=coucou"`, `hx-trigger="every 5s [window.liveIdle()]"` and `hx-select="#desk"`; the `#plant` form and `#tiles` sit outside every element that carries `hx-trigger="every 5s`
- with a waiting plant, the HTML has a poll around `#desk-coming`; with none, the string `desk-coming` is nowhere in the page
- in the browser, at the default window size, with one waiting plant in Coming: `window.liveIdle()` is true on the page as it loads (the editor's own text doesn't count); false once text is typed in the Plant box; true again once the box is emptied and focus has left it; false while the waiting plant is open
- in the browser, Dismiss on a refused note still shows "Asked" (`test_dismiss_takes_the_item_off_at_once_and_a_reload_keeps_it_off` passes unchanged)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3738
gate_failures: []
tokens: 5909176
```
