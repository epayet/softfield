---
id: f5-14-factory-look
milestone: f5-board
depends_on: []
agent: lead
difficulty: 5
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/vendor/README.md
  - docs/agents/developer.md
tests:
  - tests/factory_dashboard/test_app.py
commands: [curl]
---

### Goal
The whole dashboard takes the factory look of the mock-ups: dark by default, a light variant when the system asks for it, with the fonts self-hosted.

### Context
Read `factory_dashboard/static/dashboard.css` (its tokens and the dark override), `factory_dashboard/templates/base.html` (the top bar), the `:root` tokens and the top of `docs/milestones/f1-factory-mockup.html` (the floor, bays, plates, hazard stripe, tabs), and the board mock-up (`docs/milestones/f5-board-mockup/Main.dc.html`, `docs/milestones/f5-board-mockup/Phone.dc.html`, `docs/milestones/f5-board-mockup/Card.dc.html`: read the markup and the data in each file's script, not a page to open).
- **The tokens:** move the mock-ups' colours into the variables of `factory_dashboard/static/dashboard.css`, so every page changes at once: `--floor`, `--bay`, `--plate`, `--rule`, `--hazard`, the agent colours, `--fail`/`--clog`, and the factory and product area colours `#f2b10a` and `#4fd1a5`.
  - Dark is the default. `@media (prefers-color-scheme: light)` gives a light variant (owner, 2026-10-02): a pale floor, the same hazard yellow and orange, and ink dark enough for 4.5:1 on its plates.
  - Map the old names (`--bg`, `--surface`, `--ink`…) onto the new ones, so templates and `factory_dashboard/static/charts.js` keep working.
- **The fonts:** Chakra Petch (display), Barlow (body) and JetBrains Mono (ids and numbers), all SIL OFL.
  - Download the woff2 files once (`curl`) into `factory_dashboard/static/vendor/fonts/`, with their licences, and record them in `factory_dashboard/static/vendor/README.md`.
  - No CDN at run time (AGENTS.md rule 7).
- **The top bar:** the mock-up's title style, the hazard stripe and the tab segment, keeping today's links and the project filter. Board joins the tabs once f5-16 adds its route; leave a comment where it goes.
- Add a worked-example note to `docs/agents/developer.md`: "new UI uses the tokens, never raw colours".

### Done when
- every page renders with the new tokens, dark by default, and the light variant under `prefers-color-scheme: light` (screenshots of the Overview in both, at desktop and phone width, attached to the job's notes)
- the fonts load from `/static/vendor/fonts/`, and no page names a third-party host
- the existing dashboard tests still pass
- `uv run runner check-all --task f5-14-factory-look` passes
