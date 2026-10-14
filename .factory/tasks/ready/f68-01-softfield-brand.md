---
id: f68-01-softfield-brand
milestone: f68-i-want-the-factory-to-be
difficulty: 3
depends_on: [f17-01-status-dot-and-sign, f9-30-fix-phone-title-and-filter-one-line]
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/project.html
  - factory_dashboard/templates/_partials/logo.svg
  - factory_dashboard/static/softfield.svg
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/app.py
tests:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_projects.py
---

### Goal
The dashboard's name becomes SoftField: the top bar shows the logo and the name, both one link back to the Overview, and the page titles and the browser tab's icon say SoftField.

### Context
Read the top bar in `factory_dashboard/templates/base.html` (`.brand`), its rules in `factory_dashboard/static/dashboard.css` (`.brand`, `.brand small`, the phone `.bar-top` block), the title in `factory_dashboard/templates/project.html`, `FastAPI(title=…)` in `factory_dashboard/app.py`, and the brand tests in `tests/factory_dashboard/test_app.py` and `tests/factory_dashboard/test_projects.py`. The picture: `.factory/cards/f68-mockup/logos.html`, logo A (`#logo-a`) and the "Yellow and green" name.
- The logo is logo A's shapes, copied from the mock-up into `factory_dashboard/templates/_partials/logo.svg` and included inline in the bar, its colours from the tokens (`--good`, `--hazard`, `--hazard-ink`) so it follows the light and dark themes. `aria-hidden="true"`: the link's words name it.
- The favicon, `factory_dashboard/static/softfield.svg`, is the same shapes with fixed colours (the dark theme's), linked as `<link rel="icon" type="image/svg+xml">`.
- The name is "Soft" in `--warn-ink` (the hazard yellow on the dark floor, the deeper amber on the light one, where the yellow is too pale to read) and "Field" in `--good`, no capitals transform (the bar today uppercases it: that rule goes for the brand only). The host address (`.brand small`) stays as it is.
- The link goes to `/{{ q }}`, keeping the chosen project, as the Overview tab does; it has no underline but the name's on hover, and a 44 px tall target.
- Only what the owner sees changes: the metrics database, the backup folder, the bench cache (`runner/config.py`, `.factory/project.toml`) and the runner's commands keep "software-factory".

### Done when
- every page's top bar shows the logo and "SoftField", and its title ends "· SoftField"; no page shows "software-factory"
- clicking the logo or the name from any page (Planning with `?project=coucou`, say) opens the Overview for the same project
- the page links `softfield.svg` as its icon, and `/static/softfield.svg` serves an SVG
- at 390 px the logo, the name, F17's dot and sign, and the project select still share one row, with no layout problems (`layout_problems(page)`)
- in the light theme (`page.emulate_media(color_scheme="light")`) the logo's sprout and crate are drawn in the light tokens' colours, and "Soft" is the amber `--warn-ink`, not the hazard yellow
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
