---
id: m2-04-language-choice
milestone: 2
depends_on: []
files:
  - coucou/languages.py
tests:
  - tests/unit/test_languages.py
max_diff: 30
---

### Goal
Decide which language a paired device's screens use.

### Context
`coucou/languages.py` has this stub:

```python
def pick_language(
    kind: str, device_language: str, user_language: str, supported: Collection[str]
) -> str | None:
    raise NotImplementedError
```

The rules (ADR 00, Amendment A2):
- `kind` is `"display"`, `"phone"`, or `""` for a device nobody has claimed yet.
- A display uses its own `device_language`. A phone uses its person's `user_language`.
- `None` means "keep the language the browser asked for". Return it when the chosen language is blank, isn't in `supported`, or the kind is neither display nor phone.

`tests/unit/test_languages.py` has one case per rule.

### Pattern to follow
`coucou/reactions.py`

### Steps
1. Replace the body of `pick_language` so that every case in `tests/unit/test_languages.py` passes. This is a plain function: no Django imports.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 77
gate_failures: []
tokens: 34680  # backfilled from docs/sessions/
```
