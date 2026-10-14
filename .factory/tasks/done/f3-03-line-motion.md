---
id: f3-03-line-motion
milestone: f3
depends_on: [f3-01-factory-line]
difficulty: 4
files:
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The line moves like the old mock-up: rollers march on a belt carrying something now, a working machine's chimney smokes, and the checks light flashes green or red when a result lands, all still under reduced motion.

### Context
Read the belt, smoke and gate styles and animations in `docs/milestones/f1-factory-mockup.html` (`.belt.moving .rollers`, `@keyframes roll` and `march`, the smoke and the gate flash: the CSS and SVG to reuse), `factory_dashboard/static/factory.js` (f3-01) and `docs/milestones/f3.md` D11 ("Motion").
- `carrying` belts and `working` machines come from the document. Draw them with classes, and let CSS animate them.
- The checks light flashes once when the document's last check result differs from the one drawn before the refresh. `factory_dashboard/static/factory.js` keeps the previous one in memory, not in storage.
- Under `prefers-reduced-motion: reduce`, nothing animates: carrying belts are drawn in hazard yellow, still, and smoke is a still puff.

### Done when
- a carrying belt has the moving class and a quiet one doesn't (browser test)
- a working machine has smoke, an idle one none
- with reduced motion emulated (`page.emulate_media(reduced_motion="reduce")`), no element has a running animation
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 2173
gate_failures: ['stopped', 'stopped']
tokens: 872900
```
