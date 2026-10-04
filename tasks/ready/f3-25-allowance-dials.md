---
id: f3-25-allowance-dials
milestone: f9-line-polish
depends_on: []
difficulty: 4
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On a phone, the allowances are one row of four small dials, as in the phone mock-up, instead of four stacked bars and a legend that take most of a screen.

### Context
Read the `allowance` section of `factory_dashboard/templates/overview.html`, the `.allow`, `.meter` and `.legend` rules in `factory_dashboard/static/dashboard.css`, the allowance tests in `tests/factory_dashboard/test_overview.py` and `open_overview` there. The picture: the dials at the top of `docs/milestones/f3-line-mockup/LinePhone.dc.html` (the `dials` list in its script and the markup that draws each one: a ring filled to the percent, the window's mark, the label and the reset under it).
- **What the review saw (f3-22, `var/shots/f3-22/phone-390-light-full.png`):** under 640 px, the four windows stack as full-width bars with their legend, about 230 px tall; f3-18 asked for "one compact row".
- **Under 640 px only:** each window is a dial: its ring filled to the percent in the same colour rule as the bars (green under the mark, hazard yellow from the mark, `--fail` above 95%), the mark as a tick on the ring, the agent and its window (the same words as the bar's), the percent inside, and its reset line under it. "no data yet" shows an empty ring. Four fit in one row at 390 px. Desktop keeps today's bars.
- The legend's words stay, folded in a closed `<details>` under 640 px, as the floor's "How to read the floor".
- Keep the section id `allowance` and each row's id `allow-<label>-<window>`; `tasks/later/f4-12-allowance-top.md` relies on them. Colours through the tokens, never raw (`docs/agents/developer.md`).

### Done when
- a browser test at 390 px: the four windows' boxes share one row (same top, within 4 px) and `#allowance` is at most 160 px tall
- a browser test at 1440 px: the bars are drawn as today
- each dial's fill colour class follows the same rule as the bar's, and "no data yet" has an empty ring
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
