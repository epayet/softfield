---
id: f197-01-plant-box-asks-first
milestone: f197-reverse-plant-and-plant-and-ask
difficulty: 1
depends_on: []
files:
  - factory_dashboard/templates/planning.html
  - tests/factory_dashboard/test_planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
In the Plant box, "Plant and ask the lead" comes first in yellow and "Plant" comes second as the plain button.

### Context
The picture to build is Proposed's Plant box in `.softfield/cards/f197-mockup/plant-buttons.html`. Read `.softfield/cards/f197-reverse-plant-and-plant-and-ask.md` (D1).
- The buttons and the line beside them are in `#plant` in `factory_dashboard/templates/planning.html`.
- Keep each button's `id`, its `onclick` and its words: only their order and their `btn go` / `btn plain` classes change, so each still sends the same `ask`.
- `test_plant_only_has_btn_go` and `test_plant_ask_has_btn_plain` in `tests/factory_dashboard/test_planning.py` pin today's colours (f81-03): change them to the new ones.

### Done when
- `#plant-ask` carries `btn go` and `#plant-only` carries `btn plain`
- `#plant-ask` comes before `#plant-only` in the page
- the line beside them reads "Plant and ask the lead: the lead answers it on its thread. Plant: a seed card that waits for you; write on its thread to send it to the lead."
- "Plant and ask the lead" still sends `ask` true and "Plant" `ask` false
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 932
gate_failures: []
tokens: 232022
```
