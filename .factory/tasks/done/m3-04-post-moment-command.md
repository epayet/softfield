---
id: m3-04-post-moment-command
milestone: 3
difficulty: 3
depends_on: []
files:
  - coucou/management/commands/post_moment.py
tests:
  - tests/integration/test_post_moment.py
max_diff: 80
---

### Goal
`manage.py post_moment famille/us --note "Coucou" --photo cat.jpg` posts a test moment to a space.

### Context
`coucou/management/commands/post_moment.py` has the arguments already (`space`, `--note`, `--photo`) and a `handle` that raises `NotImplementedError`.

Everything is done by `post_content` in `coucou/services.py`:

```python
@dataclass(frozen=True)
class SpaceInfo:
    id: int
    vault_slug: str
    slug: str
    reaction_set: Sequence[str]

def post_content(repo, clock, incoming, *, space: SpaceInfo, photo: bytes | None,
                 media_root: Path, tz: tzinfo, device_id, author_id) -> Accepted: ...
```

It raises `InvalidEvent` (`coucou/intake.py`) or `InvalidPhoto` (`coucou/media.py`); both have a `.code`.

Imports you need:

```python
import uuid
from pathlib import Path
from zoneinfo import ZoneInfo
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone
from coucou.intake import EventType, IncomingEvent, InvalidEvent
from coucou.media import InvalidPhoto
from coucou.models import Space
from coucou.repos import DjangoEventRepo, SystemClock
from coucou.services import SpaceInfo, post_content
```

### Pattern to follow
`coucou/management/commands/seed_demo.py`

### Steps
1. If `settings.COUCOU_ENV == "prod"`, raise `CommandError("post_moment doesn't run in prod: it posts to real displays.")`.
2. Split `options["space"]` on the first `/` into vault slug and space slug. Look up the space with `Space.objects.select_related("vault").filter(vault__slug=..., slug=...).first()`; if none, `CommandError(f"No space {options['space']}.")`. With neither `--note` nor `--photo`, `CommandError("Give --note, --photo or both.")`. Read the photo with `Path(...).read_bytes()`; on `OSError`, `CommandError(f"No file {path}.")`.
3. Build `IncomingEvent(id=uuid.uuid4(), type=EventType.CONTENT_POSTED, created_at=now, sent_at=now, payload={"note": note} if note else {}, has_photo=photo is not None)` with `now = timezone.now()`.
4. Call `post_content(DjangoEventRepo(), SystemClock(), incoming, space=SpaceInfo(space.pk, space.vault.slug, space.slug, space.reaction_set), photo=photo, media_root=Path(settings.MEDIA_ROOT), tz=ZoneInfo(settings.TIME_ZONE), device_id=None, author_id=None)`. Turn `InvalidEvent` or `InvalidPhoto` into `CommandError(f"Refused: {exc.code}")`.
5. Finally write `f"Posted {incoming.id} to {space.vault.name} / {space.name}."` to `self.stdout`. **The prod check in step 1 comes before anything else.**

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 179
gate_failures: []
tokens: 199885
```
