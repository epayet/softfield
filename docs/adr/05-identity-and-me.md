# ADR 05: Who a device speaks for, names, and `/me/`

- **Status:** Accepted (by the owner, 2026-09-28; every item as drafted, with the owner's answers on the name screen, the redirect and timing)
- **Date:** 2026-09-28
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

After M2, the owner asked three questions:
1. Once a display is paired, who does it react as?
2. Do people set up their own details (name, avatar) on their device?
3. Can `/phone/` go? The name is too device-specific.

The owner answered each one interactively on 2026-09-28, and each item below records their choice. Item 3 amends ADR 03 item 3 (Accepted) and the wording of M2's outcome.

## Decisions

### 1. A display reacts as itself

- A reaction from a display is recorded as today (`coucou/models/events.py`): `device` = the display, and `author` = null.
- Senders see the display's label, for example "❤️ from Mum's kitchen". The owner sets the label when claiming the display.
- The display has no "who's tapping?" step. It stays one tap, which keeps it ambient.
- **To revisit** in the avatars ADR (`docs/roadmap.md`, "avatars hanging out together"). There, a display might show people rather than a place.

**Not chosen:** a "lives here" person on each display, or a person picker on the display.

### 2. People pick their name the first time they open the app

- **Model:** `User.display_name`, blank by default, at most 40 characters. The owner can still edit it in admin.
- **Screen:** the first time a person opens `/me/`, it shows a single field: "What should we call you?" / "Comment souhaitez-vous qu'on vous appelle ?" It uses `vous` (ADR 03 item 4).
  - **Required:** they confirm a name before going further. There's no "Later" button.
  - **Pre-filled** with the name the owner set in admin, if any, so it's one tap for Mum.
  - Once a name has been confirmed, a newly paired device of the same person skips the screen.
- **Changing it later:** the person can change their name later from any of their devices.
- **API:** `PATCH /api/me {display_name}`.
  - Only a personal device's session may call it, and only for its own user. A display gets 403.
  - It keeps the usual `Origin` + `X-Coucou: 1` checks.
  - It trims the value and rejects an empty one.
- **Fallback:** a name confirmed once is never blank. Until someone opens their app, anything that shows a name falls back to the username.
- **Avatars wait** for their own ADR.

**Not chosen:** a skippable form, asking only people with no name in admin, a name and an avatar together now, or names that only the owner can set in admin.

### 3. ⚑ `/phone/` becomes `/me/`, and the `phone` kind becomes `personal`

Amends ADR 03 item 3 ("`/` redirects to `/display/` or `/phone/`") and M2's outcome. The device might be a phone, a tablet or a laptop. The brief itself calls it a "member device".

- **Model:**
  - `Device.Kind.PHONE` becomes `PERSONAL = "personal", "Personal device"`.
  - A data migration rewrites existing rows from `phone` to `personal`.
  - The check constraint `device_active_assignment_matches_kind` is rebuilt with `kind="personal"`.
  - `Device.user`'s `related_name` changes from `phones` to `devices`.
- **URLs:**
  - `/` redirects a claimed personal device to `/me/`.
  - `/phone/` goes away with **no redirect**. Nothing real is paired as a phone yet (M2 isn't signed off).
  - The PWA scope and manifest (M4) live at `/me/`.
- **Words:**
  - The admin claim page asks "display or personal device?".
  - The French is "écran ou appareil personnel".
  - Code, tests and docs say "personal device" where they said "phone". Historical records stay as written: M0–M2 reviews and earlier ADRs.

**Not chosen:**
- `/app/` + `member`
- `/home/` (it could be mistaken for the display at home)
- renaming only the URL and keeping `phone` in the model

### 4. A person may have several devices; the profile lives on the person

- This already works: `Device.user` is a foreign key, so one person can pair a phone, a tablet and a laptop, each with its own key.
- Profile data (name now, avatar later) lives on `User`, never on `Device`. Any of the person's active devices can edit it, and a newly paired device sees it at once.
- Revoking one device doesn't touch the profile or the person's other devices.

## Consequences

- **A migration on `Device`,** a protected path, with isolation tests in the same commit:
  - a personal device can't change another person's name
  - a display can't change any name
  - the kind constraint still holds after the migration
- **Claude-owned changes:**
  - `models/devices.py`, `models/accounts.py` and the migration
  - `urls_public.py`
  - `views/pairing.py` and `views/auth.py`
  - `admin/devices.py` and the claim template
  - `authz.py` and `scoping.py`
- **Local-model tasks:**
  - the name form's template and strings, English and French
  - renaming "phone" in test names and fixtures
- **Lands at the start of M3,** before the display is built, so there's less to rename. Nothing in M2 has to change before sign-off.
- **Senders see places, not people,** for reactions until the avatars ADR says otherwise.
