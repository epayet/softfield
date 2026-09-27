---
id: m1-01-space-reactions-column
milestone: 1
depends_on: []
files:
  - coucou/reactions.py
  - coucou/admin/spaces.py
tests:
  - tests/unit/test_reactions.py
  - tests/integration/test_admin_lists.py
max_diff: 40
---

### Goal
Show each space's reaction set as one readable line (e.g. `❤️ 😂 😮 🥰`) in the admin's space list, and flag broken sets with `⚠ invalid`.

### Context
This is admin-only text, so it stays plain English. Don't use `gettext` and don't touch the locale files.

In `coucou/reactions.py` these already exist and must not change:

```python
DEFAULT_REACTIONS: tuple[str, ...] = ("❤️", "😂", "😮", "🥰")

class InvalidReactionSet(ValueError):
    pass

def validate_reaction_set(emojis: Sequence[str]) -> tuple[str, ...]:
    """Return the reaction set as a tuple, or raise InvalidReactionSet."""
    # Raises InvalidReactionSet for: a str, a non-Sequence (None, dict, int…),
    # fewer than 3 or more than 5 items, duplicates, or items that aren't emoji.
```

The stub to implement, at the bottom of `coucou/reactions.py`:

```python
def format_reaction_set(value: object) -> str:
    """The reaction set as one line for admin lists, e.g. ``"❤️ 😂 😮 🥰"``.

    Returns ``"⚠ invalid"`` when ``value`` isn't a valid reaction set.
    """
    raise NotImplementedError
```

`coucou/admin/spaces.py` currently contains (the imports at the top are `from django import forms`, `from django.contrib import admin` and `from coucou.models import Membership, Space`):

```python
@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin[Space]):
    form = SpaceForm
    list_display = ["name", "vault", "slug"]
    list_filter = ["vault"]
    prepopulated_fields = {"slug": ["name"]}
    filter_horizontal = ["controllers"]

    @admin.display(description="Reactions")
    def reactions(self, obj: Space) -> str:
        raise NotImplementedError
```

`Space.reaction_set` is a `JSONField`, so at runtime it can hold anything (normally a list of str).

What the tests expect:
- `format_reaction_set(DEFAULT_REACTIONS) == "❤️ 😂 😮 🥰"` (items joined by a single space)
- `format_reaction_set(["🙏", "👍🏽", "1️⃣"]) == "🙏 👍🏽 1️⃣"`
- `format_reaction_set(x) == "⚠ invalid"` for `None`, `{}`, `42`, `"❤️😂😮"`, `["❤️", "😂"]`, `["❤️", "❤️", "😮"]`, `["a", "b", "c"]`
- `"reactions" in SpaceAdmin.list_display`, and `SpaceAdmin(...).reactions(space)` returns `format_reaction_set(space.reaction_set)`

### Pattern to follow
`coucou/reactions.py`: small typed functions with a one-line docstring.

### Steps
1. In `coucou/reactions.py`, implement `format_reaction_set(value: object) -> str`: call `validate_reaction_set(value)` inside `try`/`except InvalidReactionSet`, return `"⚠ invalid"` on the exception, otherwise return `" ".join(...)` of the validated tuple. `validate_reaction_set` expects `Sequence[str]`, so to satisfy mypy strict, first return `"⚠ invalid"` when `not isinstance(value, Sequence)` (the `Sequence` import already exists), then pass `value` on.
2. In `coucou/admin/spaces.py`, add `from coucou.reactions import format_reaction_set`, make the `reactions` method `return format_reaction_set(obj.reaction_set)`, and add `"reactions"` to the end of `list_display`.
3. Run `uv run pytest -q tests/unit/test_reactions.py tests/integration/test_admin_lists.py`, then `uv run ruff format coucou/reactions.py coucou/admin/spaces.py`, `uv run ruff check coucou/reactions.py coucou/admin/spaces.py` and `uv run mypy coucou`.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
logs: var/runs/20260927-234410/m1-01-space-reactions-column
```
