---
id: f3-20-machines-and-belts
milestone: f3
depends_on: [f3-19-crate-details]
difficulty: 4
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The machines and belts read like the mock-ups:
- each machine carries a LOCAL or CLOUD plate and its rating, readable at a glance;
- a working machine blinks a row of three lights;
- the belts show yellow dotted rollers where work went today, marching where it goes now.

### Context
Read `machine` and `belt` in `factory_dashboard/static/factory.js`, the floor rules in `factory_dashboard/static/dashboard.css` (`.floor .belt …`, `.machine.on …`, the `prefers-reduced-motion` block) and the browser tests in `tests/factory_dashboard/test_line.py`. The pictures:
- `docs/milestones/f1-factory-mockup.html`: the CSS rules `.machine .plate.local`, `.plate.cloud`, `.ptext.*`, `.machine .led`, `@keyframes led`, and the script that draws the `led` rects (search `class: "led"`);
- `docs/milestones/f3-line-mockup/Line.dc.html`: the developer bay's machines and the belts' `stroke="#f2b10a" stroke-dasharray="2 7"`.

Read the markup and CSS. These are not pages to open.
- **Why (owner, 2026-10-03):**
  - "The cloud vs local label was clear, the three moving lines when it's working was clear, the rating of the model was clear."
  - "I like the yellow dotted lines; in the mock-up they are in the factory lines as well."
- **The plate:** each developer and reviewer machine shows a plate under its name. Use the f1 mock-up's style, solid for LOCAL and outlined for CLOUD, with `m.where` in capitals (`local GPU`, `Ollama cloud`, `Claude`, `Copilot`: the plate is `local` for `local GPU`, else `cloud`), and `· rated N` (or `· not rated yet` when `m.rating` is null). Today these are small dim words.
- **Three lights:** a working machine (`m.state === "working"`) has three small lights beside its name that blink in turn (the mock-up's `led` animation, 0.15 s apart). They are off on an idle machine. Under `prefers-reduced-motion`, they stay lit and still.
- **Belts:**
  - A belt with `today > 0` has the yellow dotted rollers (`#f2b10a` through a token in `factory_dashboard/static/dashboard.css`, not a raw colour in the script), still and a little dimmer.
  - A `carrying` belt has them bright and marching, as today's `roll`.
  - A belt with nothing today keeps the grey rollers.
- Keep f3-17's rule: same nodes across refreshes, so nothing restarts.

### Done when
- a browser test: a LOCAL machine's plate and a CLOUD machine's plate differ (class `local` / `cloud`) and show "rated N" or "not rated yet"
- a browser test: a working machine has three lights with a running animation; an idle one's are off; under reduced motion none animates
- a browser test: a belt with today's trips but not carrying has the yellow rollers and no animation; a carrying belt has them animated
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
