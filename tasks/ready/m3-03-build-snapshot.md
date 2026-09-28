---
id: m3-03-build-snapshot
milestone: 3
depends_on: []
files:
  - coucou/snapshot.py
tests:
  - tests/unit/test_snapshot.py
max_diff: 40
---

### Goal
Build the part of a display's snapshot that says what to show: the current moment, the reactions on it, and the reaction set.

### Context
`coucou/snapshot.py` has the dataclasses `MomentRow` and `ReactionRow`, the constant `RECENT_REACTIONS = 20`, two finished helpers that turn one row into its JSON dict:

```python
def moment_json(moment: MomentRow) -> dict[str, Any]: ...
def reaction_json(reaction: ReactionRow) -> dict[str, Any]: ...
```

and this stub:

```python
def build_snapshot(
    moments: Sequence[MomentRow],
    reactions: Sequence[ReactionRow],
    reaction_set: Sequence[str],
    *,
    limit: int = RECENT_REACTIONS,
) -> dict[str, Any]:
    raise NotImplementedError
```

Which moment is current is already decided by `coucou/ordering.py`:

```python
@dataclass(frozen=True)
class ContentRef:
    event_id: uuid.UUID
    effective_at: datetime
    received_at: datetime

def current_content(candidates: Iterable[ContentRef]) -> ContentRef | None: ...
```

The result has exactly three keys:
- `moment`: `None` when there are no moments, else `moment_json(current)`.
- `reactions`: `reaction_json(r)` for the reactions whose `target` is the current moment's `id`, newest `effective_at` first, at most `limit`.
- `reaction_set`: a list.

`tests/unit/test_snapshot.py` shows every case.

### Pattern to follow
`coucou/ordering.py`

### Steps
1. Implement `build_snapshot` so every test in `tests/unit/test_snapshot.py` passes.
2. **Choose the current moment with `current_content`, never your own sort, and build every dict with `moment_json` and `reaction_json`: these rules must stay in one place.** It's a plain function: no Django imports.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
