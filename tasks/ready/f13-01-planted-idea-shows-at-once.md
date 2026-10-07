---
id: f13-01-planted-idea-shows-at-once
milestone: f13-planting-idea-ui-feedback
difficulty: 3
depends_on: []
files:
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On `/planning`, pressing "Plant it" shows the idea in Coming at once, as on its way, and clears the form, instead of only "Asked: the runner will do it." under the button.

### Context
Read `factory_dashboard/templates/planning.html`: the `#plant` form posts a `plant` request to `/requests` and puts `factory_dashboard/templates/_partials/request.html` in `#plant-status`; `#desk-coming` is drawn only when the page loads, and only when it has items.
- `coming` in `factory_dashboard/planning.py` already lists every open `plant` request as "planting at the runner's next pick", and `.desk-coming` in `factory_dashboard/static/dashboard.css` gives it the dashed orange edge. Nothing changes server-side.
- The owner (2026-10-07): "I want to see the coming box straight away without having to reload."
- Wrap the form and `#desk-coming` in one element (`#plant-row`). Once the request is stored (`hx-on::after-request`, on success only), re-fetch `/planning` into `#plant-row` with `hx-select="#plant-row"` and `hx-swap="outerHTML"`: Coming appears with the new idea and the form comes back empty.
- Keep the Desk out of the swapped element, so the page doesn't jump.
- Example to follow: the thread's Send in `factory_dashboard/templates/thread.html` (`#conversation`, f6-21), and its browser test in `tests/factory_dashboard/test_planning.py`.
- `test_the_plant_form_posts_a_plant_request` waits for "Asked" in `#plant-status`; change its wait to the new Coming row.

### Done when
- a browser test: with nothing in Coming, typing a title and pressing Plant it shows `#desk-coming` holding that title and "planting at the runner's next pick", without a reload; the title and thoughts fields are empty afterwards
- a second plant adds a second row, after the first
- a failed post (the request refused) leaves the form as typed and Coming as it was
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
