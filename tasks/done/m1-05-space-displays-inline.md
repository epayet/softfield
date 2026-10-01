---
id: m1-05-space-displays-inline
milestone: 1
difficulty: 2
depends_on: []
files:
  - coucou/admin/spaces.py
tests:
  - tests/integration/test_admin_space_displays.py
max_diff: 30
---

### Goal
A space's edit page lists its displays read-only (label, status, language), each with a link to its device page.

### Context
Admin-only text: plain English, no `gettext`.

In `coucou/admin/spaces.py` (it already imports `admin` and `Device, Membership, Space`):

```python
class DisplayInline(admin.TabularInline[Device, Space]):
    """The space's displays, read-only. Pairing and revoking happen on the device page."""

    model = Device
    fk_name = "space"
```

`class SpaceAdmin` ends with `filter_horizontal = ["controllers"]` followed by its `reactions` method.

**Security rule:** the inline shows only `label`, `status` and `language`. Never show `public_key_spki`, `pairing_code_hash` or `pairing_expires_at`.

### Pattern to follow
`coucou/admin/accounts.py` (its `MembershipInline`)

### Steps
1. Add `from django.http import HttpRequest`.
2. In `DisplayInline`, set `fields = ["label", "status", "language"]` and `readonly_fields = ["label", "status", "language"]`, plus `show_change_link = True`, `can_delete = False` and `extra = 0`.
3. Add `def has_add_permission(self, request: HttpRequest, obj: Space | None = None) -> bool:` returning `False`.
4. In `SpaceAdmin`, add `inlines = [DisplayInline]` right after `filter_horizontal`.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 54
gate_failures: []
tokens: 54682  # backfilled from docs/sessions/
```
