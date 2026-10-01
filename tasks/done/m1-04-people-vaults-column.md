---
id: m1-04-people-vaults-column
milestone: 1
difficulty: 2
depends_on: []
files:
  - coucou/admin/accounts.py
tests:
  - tests/integration/test_admin_people.py
max_diff: 30
---

### Goal
The admin's people list shows which vaults each person is in, e.g. `Amis, Famille`.

### Context
Admin-only text: plain English, no `gettext`.

In `coucou/admin/accounts.py`, `class CoucouUserAdmin` currently has:

```python
    fieldsets = (*(UserAdmin.fieldsets or ()), ("Coucou", {"fields": ("language",)}))
    list_display = ("username", "first_name", "language", "is_staff")

    @admin.display(description="Vaults")
    def vaults(self, obj: User) -> str:
        raise NotImplementedError
```

`Membership` has `user` (with `related_name="memberships"`) and `vault` foreign keys. `Vault` has a `name`.

The test allows at most 3 queries for the whole list, so the vaults must be prefetched.

### Pattern to follow
`coucou/admin/spaces.py`

### Steps
1. Add imports if they're missing: `from django.db.models import QuerySet` and `from django.http import HttpRequest`.
2. Add `def get_queryset(self, request: HttpRequest) -> QuerySet[User]:` returning `super().get_queryset(request).prefetch_related("memberships__vault")`.
3. `vaults` returns `", ".join(sorted(m.vault.name for m in obj.memberships.all()))`. Use `.all()`, not `.filter()`, so the prefetch is used. Someone in no vault gets `""`.
4. Add `"vaults"` to the end of `list_display`.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 63
gate_failures: []
tokens: 46049  # backfilled from docs/sessions/
```
