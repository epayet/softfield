---
id: f256-02-words-on-one-line
milestone: f256-the-alignments-of-the-top-bar
difficulty: 2
depends_on: []
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/_partials/bar_status.html
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
On a wide screen every word in the top bar's top row has the middle of its capitals on the row's centre line: the brand's name, the host, the status words, and each plate's key and value (Job, On, Project), the project's name included.

### Context
Read `.softfield/cards/f256-the-alignments-of-the-top-bar.md` ("Round 2", D6 to D8) and build the Proposed of `.softfield/cards/f256-mockup/text-line.html`: its CSS under "PROPOSED" is the picture to copy, on the tokens of `factory_dashboard/static/dashboard.css`.
- `factory_dashboard/static/dashboard.css`: the top bar's rules (`.brand small`, `.factory-status .words`, `.factory-status .uptime` and `.job` with their `.key` and `.val`, `.bar-top .filters`) and the phone block `@media (max-width: 639px)`, whose look doesn't change: its key stays hidden and the plate's `.val` names the project where the bare select did.
- `factory_dashboard/templates/_partials/bar_status.html`: the Job and On plates take the shared `tag` class; their ids, titles and `aria-hidden` lines stay.
- `factory_dashboard/templates/base.html`: the `filters` form's label gets the project's name as `<span class="val">` with a caret, and the select lies over the plate unseen; keep its `name`, `onchange`, the `<noscript>` button, and give it `aria-label="Project"`.
- `tests/factory_dashboard/test_app.py` drives the real page with Playwright (`test_at_390px_the_top_bar_is_no_taller` shows the routing). A text's capital middle is its baseline minus half its cap height: the baseline is the top of a zero-size `inline-block` appended to the element, the cap height `measureText("H").actualBoundingBoxAscent` on a canvas set to the element's computed font.

### Done when
- at 1280 px, in both themes, with a developer job running (so the Job plate shows "… min" and an attempt), the capital middles of the brand's name, the host, the status words, each plate's key and value and the project's name are all within 1 px of the top row's centre
- clicking anywhere on the Project plate opens the list, and choosing a project reloads the page with it, as today
- the plate shows a focus ring when the list has the keyboard's focus
- at 390 px the top bar is no taller than before, and the project's name shows without its key
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
