---
id: f13-01-planted-idea-shows-at-once
milestone: f13-planting-idea-ui-feedback
difficulty: 3
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/templates/planning.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On `/planning`, pressing Plant (or Plant and ask the lead) shows the idea in Coming at once, as on its way, and clears the form, instead of only "Asked: the runner will do it." under the buttons.

### Context
Read `factory_dashboard/templates/planning.html`: the `#plant` form posts a `plant` request to `/requests` and puts `factory_dashboard/templates/_partials/request.html` in `#plant-status`; `#desk-coming` is drawn only when the page loads, and only when it has items.
- The form has one box, the textarea named `text`, and two submit buttons: Plant (`#plant-only`) and Plant and ask the lead (`#plant-ask`). Both must show the idea at once.
- `coming` in `factory_dashboard/planning.py` already lists every open `plant` request as "planting at the runner's next pick", and `.desk-coming` in `factory_dashboard/static/dashboard.css` gives it the dashed orange edge. Nothing changes server-side.
- Coming's title for a one-box note is the whole note on one line (line breaks become spaces) when it is under 60 characters, so a short one-line note shows as typed.
- The owner (2026-10-07): "I want to see the coming box straight away without having to reload."
- Wrap the form and `#desk-coming` in one element (`#plant-row`), styled `display: contents` so the layout stays as today. Once the request is stored (`hx-on::after-request` on the form, on success only), re-fetch `/planning` into `#plant-row`, selecting `#plant-row` from the answer and swapping its outer HTML: Coming appears with the new idea and the form comes back empty.
- The handler goes on the form, not on `#plant-row`: the re-fetch fires its own after-request event on its target, and a handler there would re-fetch forever.
- Keep the Desk out of the swapped element, so the page doesn't jump.
- Example to follow: the thread's Send in `factory_dashboard/templates/thread.html` (`#conversation`, f6-21), and its browser test `test_send_with_comments_posts_one_request` in `tests/factory_dashboard/test_planning.py`.
- `test_the_plant_form_posts_a_plant_request` waits for "Asked" in `#plant-status`; change its wait to the new Coming row, and keep its two buttons and its database assertion.
- To refuse a post in a browser test: a `page.route` registered after `_open` is tried before `_open`'s own; fulfil the post to `/requests` with status 400.

### The branch so far (the lead read it, 2026-10-10)
Your branch already holds the wrapper, the CSS rule, the handler on the form and three new tests. Don't start again and don't re-read the server side: `/requests` adds one new row per plant, and `coming` lists every open one. What is left is small:
- The last attempt failed the `layout` gate on a file that was never yours, a scratch file on main. This ticket now waits for the ticket that removes it, so that gate is clean when you start.
- Your second plant was stored. `test_a_second_plant_adds_a_second_row` read "Coming · 1" because its second `page.wait_for_selector("#desk-coming")` returns at once: the section is already on the page from the first plant, so the test reads the page before the second re-fetch lands. Wait for something only the second re-fetch brings, as `test_send_with_comments_posts_one_request` waits for its own message's text (`#conversation >> text=And the phone?`).
- The handler on the branch swaps `innerHTML`; this ticket says the outer HTML. With a `select` of `#plant-row`, htmx puts the selected element itself inside the target.
- The branch adds a second `_coming_text` to `tests/factory_dashboard/test_planning.py`; the file already had one, a few lines below `_coming_items`. Keep one.
- `test_a_failed_post_leaves_textarea_and_coming_as_they_were` asserts straight after the click, before the refused answer has come back, so it passes whatever the page does next. Playwright's `with page.expect_response(...)` around the click waits for an answer.
- In that test's `refuse`, `route.continue_()` sends a request to the real network, where nothing listens; `route.fallback()` hands it on to `_open`'s handler.

### Done when
- a browser test: with nothing in Coming (`#desk-coming` absent), typing a note and pressing Plant shows `#desk-coming` holding that note as its title and "planting at the runner's next pick", without a reload; the textarea is empty afterwards
- after that plant the page holds exactly one `#plant-row`, one `#plant` and one `#desk-coming` (a count of each, so a wrapper nested in itself fails)
- a second plant adds a second row, after the first: Coming's titles, in order, are the two notes, and its heading reads "Coming · 2"
- a failed post (the request refused): the test waits for the refused answer, then the textarea is as typed and Coming is as it was. Start it with one idea already planted, so "as it was" is one row, not an absent section
- `tests/factory_dashboard/test_planning.py` defines `_coming_text` once
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: layout)
attempts: 3
tokens: 2837235
logs: var/runs/20261010-085423/f13-01-planted-idea-shows-at-once
```

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 6817779
logs: var/runs/20261013-135255/f13-01-planted-idea-shows-at-once
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
