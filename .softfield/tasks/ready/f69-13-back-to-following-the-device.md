---
id: f69-13-back-to-following-the-device
milestone: f69-i-want-a-button-to-switch
agent: lead
difficulty: 3
depends_on: [f69-11-fix-theme-switch-plate-tests-tests]
files:
  - factory_dashboard/templates/base.html
tests:
  - tests/factory_dashboard/test_app.py
area: factory
---

### Goal
The theme switch follows the device by default, and a choice made with it is only an override: it ends when it matches the device again, or when the device next changes its theme.

### Context
Read the two theme scripts in `factory_dashboard/templates/base.html` (the one in `<head>` before the stylesheet, and the switch's click handler) and the f69 tests in `tests/factory_dashboard/test_app.py` (from "theme switch button"). Decisions are in `.softfield/cards/f69-i-want-a-button-to-switch.md` ("Follow the device, override by hand"). Nothing on screen changes but the switch's hover title.
- **Pressing the switch:** the next theme is set as today. If it is the device's own theme (`matchMedia("(prefers-color-scheme: light)")`), the stored `theme` is removed and the page follows the device again; else the next theme is stored.
- **The device changes its theme:** the listener is always attached (today it is only when nothing was stored at load, so an override never ends). On a change, the stored `theme` is removed and the page takes the device's theme, moving the knob and dispatching `themechange` as now.
- **The title** says which it is: "Night theme, as your device · switch to the light theme" while following, "Night theme, your choice until your device changes · switch to the light theme" while overridden (the same with Light / night).
- `aria-checked` and `themechange` behave as now.

### Done when
- with nothing stored, the page follows the device, and a device change moves the switch
- pressing it away from the device's theme stores the choice and survives a reload; pressing it back removes the stored choice
- a device change while overridden removes the stored choice and shows the device's theme
- the title says "as your device" or "your choice until your device changes", whichever holds
- the listed `tests:` pass, and fail without the change
- all gates pass
