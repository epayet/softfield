---
id: m1-02-seed-demo
milestone: 1
difficulty: 3
depends_on: []
files:
  - coucou/management/commands/seed_demo.py
tests:
  - tests/integration/test_seed_demo.py
max_diff: 100
---

### Goal
Implement `manage.py seed_demo`: it creates a small demo world (vault "Famille", Mum and me as members, space "Us" with me as controller, one display waiting to be paired) and is safe to run again.

### Context
This is a developer/admin command, so its output is plain English. Don't use `gettext` and don't touch the locale files.

The stub to implement is all of `coucou/management/commands/seed_demo.py` (`coucou/management/__init__.py` and `coucou/management/commands/__init__.py` already exist):

```python
"""``manage.py seed_demo``: a small demo world for trying Coucou in the admin. Safe to rerun."""

from typing import Any

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the demo vault 'Famille' with Mum, me, the space 'Us' and one display."

    def handle(self, *args: Any, **options: Any) -> None:
        raise NotImplementedError
```

The models are all importable with `from coucou.models import Device, Membership, Space, User, Vault`. They are defined in `coucou/models/accounts.py` (User, Vault, Membership), `coucou/models/spaces.py` (Space) and `coucou/models/devices.py` (Device). Only the fields you need are shown:

```python
class User(AbstractUser):  # coucou/models/accounts.py
    language = models.CharField(
        max_length=8, choices=settings.LANGUAGES, default="en"
    )  # "en" or "fr"
    # plus AbstractUser's username, first_name, set_unusable_password(), save() …


class Vault(models.Model):  # coucou/models/accounts.py
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=60, unique=True)


class Membership(models.Model):  # coucou/models/accounts.py; unique on (user, vault)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name="memberships")


class Space(models.Model):  # coucou/models/spaces.py; unique on (vault, slug)
    vault = models.ForeignKey(Vault, on_delete=models.CASCADE, related_name="spaces")
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=60)
    controllers = models.ManyToManyField(User, blank=True, related_name="controlled_spaces")
    reaction_set = models.JSONField(default=_default_reactions)  # leave the default


class Device(models.Model):  # coucou/models/devices.py
    class Kind(models.TextChoices):
        DISPLAY = "display", "Display"
        PHONE = "phone", "Phone"

    class Status(models.TextChoices):
        PENDING = "pending", "Waiting to be paired"
        ACTIVE = "active", "Active"
        REVOKED = "revoked", "Revoked"

    kind = models.CharField(max_length=10, choices=Kind.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    label = models.CharField(max_length=80, blank=True)
    public_key_spki = models.BinaryField()
    fingerprint = models.CharField(max_length=19)
    pairing_code_hash = models.CharField(max_length=64, blank=True)
    space = models.ForeignKey(
        Space, null=True, blank=True, on_delete=models.CASCADE, related_name="displays"
    )
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE, related_name="phones"
    )
```

**Security rule:** the demo display must stay `PENDING` with an empty key (`public_key_spki=b""`), an empty `fingerprint` and an empty `pairing_code_hash`. Never create an `ACTIVE` device and never invent keys or pairing codes: pairing is Claude-only (M2).

What the tests in `tests/integration/test_seed_demo.py` check:
- users `me` (language `"en"`, first name `"Me"`) and `mum` (language `"fr"`, first name `"Mum"`), both with unusable passwords
- an existing user with the same username is kept as-is: don't change its name, language or password
- vault slug `famille`, name `Famille`; exactly those two members
- space slug `us`, name `Us`, in that vault; controllers are exactly `[me]`
- exactly one `Device`: kind display, status pending, space `us`, user `None`, label `"Mum's kitchen"`, empty key and empty `pairing_code_hash`
- running the command twice leaves the same counts (1 vault, 2 memberships, 1 space with 1 controller, 1 device)
- output: the first run's stdout contains `Famille`; a second run's stdout contains `already` (any case)

### Pattern to follow
`tests/integration/conftest.py`: its `_world` function creates the same kinds of objects with the ORM.

### Steps
1. In `handle`, use `get_or_create` for everything, and track whether anything was created:
   - users: for `("me", "Me", "en")` and `("mum", "Mum", "fr")`, `User.objects.get_or_create(username=..., defaults={"first_name": ..., "language": ...})`. Only when created, call `user.set_unusable_password()` and `user.save()`.
   - `Vault.objects.get_or_create(slug="famille", defaults={"name": "Famille"})`
   - `Membership.objects.get_or_create(user=..., vault=vault)` for both users
   - `Space.objects.get_or_create(vault=vault, slug="us", defaults={"name": "Us"})`, then `space.controllers.add(me)` (adding twice is harmless)
   - `Device.objects.get_or_create(kind=Device.Kind.DISPLAY, space=space, label="Mum's kitchen", defaults={"status": Device.Status.PENDING, "public_key_spki": b"", "fingerprint": ""})`
2. Output with `self.stdout.write(...)`: if anything was created, `"Demo data ready: vault 'Famille', space 'Us', Mum's kitchen display (waiting to be paired)."`, otherwise `"Demo data is already there; nothing changed."`
3. Wrap the body in `with transaction.atomic():` (`from django.db import transaction`).
4. Run `uv run pytest -q tests/integration/test_seed_demo.py`, then `uv run ruff format` and `uv run ruff check` on the file, and `uv run mypy coucou`.

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 82
gate_failures: []
tokens: 89533  # backfilled from docs/sessions/
```
