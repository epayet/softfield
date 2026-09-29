---
id: m4-05-me-css
milestone: 4
depends_on: [m4-01-compose-note, m4-02-compose-photo, m4-04-delivery-list]
files:
  - coucou/static/coucou/css/me.css
  - coucou/templates/coucou/me.html
tests:
  - tests/browser/test_me.py
---

### Goal
Style `/me/` for a phone: the name screen, `Compose` and `Delivery`.

### Context
Follow `coucou/static/coucou/css/pair.css` (a phone-first page) and its link in the templates; `coucou/templates/coucou/me.html` links `me.css`. The markup comes from `coucou/static/coucou/js/name_form.js`, `coucou/static/coucou/js/compose.js` and `coucou/static/coucou/js/delivery.js`: read them for the classes and ids.
- Mobile first, one column, a comfortable reading size, large tap targets (at least 44 px high) for every button and input, including the file buttons, the picker and Try again / Remove.
- The photo preview and the delivery thumbnails never overflow the width; a warm, calm look consistent with `pair.css`.
- The `hidden` attribute must really hide (see `test_hidden_really_hides` in `tests/integration/test_display_css.py`).
- Self-hosted only: no fonts or assets from elsewhere.

### Done when
- `layout_problems(page) == []` at `PHONE` for: the name screen; `Compose` with a 280-character note, a previewed photo and two spaces; `Delivery` with one item per status (a refused one with its buttons and a long note)
- every button and input on those screens is at least 44 px high (checked in a browser test)
- `[hidden]` elements are hidden
- the listed `tests:` pass, and fail without the change
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
