# ADR 03: Pairing details ADR 00 leaves open

- **Status:** Accepted (by the owner, 2026-09-28; every option below was chosen by the owner)
- **Date:** 2026-09-28
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

ADR 00 §2.3–2.4 fixes the pairing and session protocol. Building M2 turned up choices it doesn't settle. The owner went through them interactively, and each item records the option chosen. The Claude-only protocol work (M2 items C1–C6) doesn't depend on any of them.

## Decisions

### 1. ⚑ WhiteNoise serves the public app's static files, from M2

**Why now:** the backlog said to decide static serving in M3, with no new dependency by default. The pairing page needs its JS and CSS in M2.

**Decision:**
- Add **WhiteNoise** as a runtime dependency, used by the public process only. It's mature, and it gives compression and, later, versioned file names (useful for M3's service worker) for free.
- Only `collectstatic` output under `STATIC_ROOT` is served. Nothing from `MEDIA_ROOT`, and the admin process's static files never reach the public app.

**Not chosen:** a small hand-written view with no dependency, or deferring to M3 (M2 would stall).

### 2. ⚑ Session cookie over plain `http://localhost` (dev and staging only)

**The problem:** `__Host-coucou_s` (ADR 00 §2.3) requires `Secure`, which WebKit may refuse on `http://localhost`.

**Decision:**
- **Prod** always uses `__Host-coucou_s` with `Secure`. A settings test asserts this.
- **Dev and staging** use `coucou_s` without `Secure`, **only if** `COUCOU_PUBLIC_ORIGIN` is `http://localhost…` or `http://127.0.0.1…`.

### 3. ⚑ One pairing URL; the kind is chosen when claiming

Changes ADR 00 §2.4, where the device sends `kind` when it registers.

- **Every device pairs at `/`.** Registration sends only `{public_key_spki, app_version}`, and the device stays kind-less while it's pending.
- **The claim sets the kind:** when you claim a device in admin, you assign it to a space (it becomes a display) or to a person (it becomes a phone).
- **After the claim, `/` redirects** to `/display/` or `/phone/`. Each app keeps its own service-worker scope and manifest, so a home-screen icon opens the right one.
- **Nobody types a per-kind address:** Mum and your sister only need one link.
- **Pairing text is kind-neutral:** "this device", "cet appareil".
- **Model change:** `Device.kind` becomes blank while pending. The "active assignment matches kind" constraint stays as it is.

**Not chosen:** `/display/` and `/phone/` as pairing URLs, `/d/` and `/p/`, or a picker screen.

### 4. The pairing screen uses `vous`

- French uses **`vous`**. It stays neutral if people outside the family ever pair a device.
- There's no owner-name setting. For example: "Pour relier cet appareil, donnez ce code à la personne qui a installé Coucou."

**Not chosen:** `tu` with or without your name.

### 5. Expired codes aren't renewed automatically

A code lasts 10 minutes. When it expires, the screen offers **"Obtenir un nouveau code" / "Get a new code"**, and a new code is issued only when someone taps it. A display left on the pairing screen overnight never reaches the limit of 20 registrations a day.

### 6. ⚑ Browser tests (Playwright) wait for M3

Changes when ADR 00 §2.9's first flow ("pair a display and a phone") gets automated, not whether it does.

- **Signature vectors:** a dev-only page (never routed in prod) signs a fixed message with WebCrypto. The owner opens it once in desktop Chrome and once in iPhone Safari, and pastes the JSON it shows. Those vectors become committed fixtures for the unit tests. This covers the riskiest interoperability point: raw `r‖s` → DER.
- **M2's e2e:** `pytest -m e2e` on staging runs the existing smoke tests, plus an HTTP-level pairing test that drives the API with signatures made in Python.
- **The browser flow** is checked by hand at sign-off: a real Android display and a real iPhone.
- **Playwright's browsers are downloaded in M3,** when offline caching, the outbox and the service worker make manual checks costly.

## Consequences

- One new runtime dependency (WhiteNoise). The backlog item "public static serving" is closed.
- Prod's cookie stays exactly as ADR 00 says; only localhost gets the fallback.
- A pending device has no kind. The admin claim form decides it, and the pairing screens are kind-neutral.
- M2 has no automated browser test. The owner's real-device pairing and the captured vectors stand in until M3.
