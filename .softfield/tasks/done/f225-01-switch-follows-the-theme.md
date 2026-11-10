---
id: f225-01-switch-follows-the-theme
milestone: f225-there-is-a-tiny-amount-of
difficulty: 2
depends_on: []
files:
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The night/light switch no longer slides when a page loads: its knob is in the right place from the first paint, and it still slides when the theme changes.

### Context
Read the Decisions in `.softfield/cards/f225-there-is-a-tiny-amount-of.md`.
- In `factory_dashboard/static/dashboard.css`, the `.theme-switch` rules place the knob and light the icon from `aria-checked`. The attribute is only right after `DOMContentLoaded`, whereas `data-theme` on `<html>` is right before the first paint. Key them on the theme instead, as `:root[data-theme="light"] .floor .bar-fill` in the same file does; anything not light is night, as in the script in `factory_dashboard/templates/base.html`.
- There are three rules: the knob's place, the lit icons, and the knob's place again in the phone rules (`calc(100% - 19px)`). Keep the `transition` rule as it is.
- Leave `factory_dashboard/templates/base.html` alone: its script still sets `aria-checked` and the title.
- The theme tests are in `tests/factory_dashboard/test_app.py`; follow `test_the_theme_button_says_night_when_dark` for loading a page.
- A trap in the test: how fast a page paints decides whether the old slide shows, so a test that only watches a load can pass on the old code. Test the cause, under `page.emulate_media(reduced_motion="reduce")` so that positions settle at once: with `aria-checked` changed by hand to disagree with the theme, the knob must not move.

### Done when
- in the night theme, with `aria-checked` set by hand to `false`, the knob stays at the top of the plate and the moon stays lit; in the light theme, with it set to `true`, the knob stays at the bottom and the sun stays lit
- the same holds at 390 × 844, where the knob's place has its own rule
- loading a page in the night theme starts no `transitionrun` on the knob (listened for with `page.add_init_script`, before the page loads)
- pressing the switch still starts a `transitionrun` on the knob, and the knob ends on the other side
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: task-tests)
attempts: 3
tokens: 3341923
logs: .softfield/var/runs/20261106-011143/f225-01-switch-follows-the-theme
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
