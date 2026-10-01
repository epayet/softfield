---
id: m1-03-vault-list-counts
milestone: 1
difficulty: 1
depends_on: []
files:
  - coucou/admin/accounts.py
tests:
  - tests/integration/test_admin_vaults.py
max_diff: 40
---

### Goal
The admin's vault list shows how many members and spaces each vault has.

### Context
Admin-only text: plain English, no `gettext`.

In `coucou/admin/accounts.py`, `class VaultAdmin` currently has:

```python
    list_display = ["name", "slug", "created_at"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [MembershipInline]

    @admin.display(description="Members", ordering="member_count")
    def members(self, obj: Vault) -> int:
        raise NotImplementedError

    @admin.display(description="Spaces", ordering="space_count")
    def spaces(self, obj: Vault) -> int:
        raise NotImplementedError
```

`Membership` and `Space` both point at `Vault` with `related_name="memberships"` and `related_name="spaces"`.

### Pattern to follow
`coucou/admin/spaces.py`

### Steps
1. Add imports: `from django.db.models import Count, QuerySet` and `from django.http import HttpRequest`.
2. Add `def get_queryset(self, request: HttpRequest) -> QuerySet[Vault]:` returning `super().get_queryset(request).annotate(member_count=Count("memberships", distinct=True), space_count=Count("spaces", distinct=True))`.
3. `members` returns `int(getattr(obj, "member_count", 0))`, and `spaces` returns `int(getattr(obj, "space_count", 0))`. The `getattr` keeps mypy happy.
4. Add `"members", "spaces"` to the end of `list_display`.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 89
gate_failures: []
tokens: 45131  # backfilled from docs/sessions/
```
