# ADR 00: Initial architecture and workflow

- **Status:** Accepted (by the owner, 2026-09-27)
- **Date:** 2026-09-27
- **Deciders:** project owner (accepts), Claude (drafts)
- **Supersedes:** the original brief (`docs/original-brief.md`) once Accepted

## Context

Coucou is a privacy-first "ambient presence" system. People send small moments (a photo and/or a short note) to always-on displays in family homes, and recipients tap to react. The first real use is one vault (owner + Mum), one space ("Us") and two displays. A sister on iPhone joins soon after.

The system runs on the owner's Linux desktop and is exposed only through Tailscale Funnel. The machine is sometimes off, so clients must be offline-first.

The build is done by Claude (architect, protected paths, reviews) and a local Qwen model through OpenCode (small tasks), coordinated by a deterministic runner.

This ADR records the decisions already made in the brief (§1) and recommends the open choices (§2). Items marked **⚑** deviate from, or sharpen, the brief and need explicit approval.

---

## 1. Decisions carried over from the brief

| Area | Decision |
|---|---|
| Slug | `coucou` for the repo, Python package and Django project. "Vault" is internal only. |
| Language/tooling | Python managed entirely with **uv**. **Python 3.13** (uv-managed; the system Python is 3.10). |
| Framework | **Django 5.2 LTS**; Django admin for all management in the MVP. |
| Real-time | **Django Channels** over WebSockets, with the in-memory channel layer (see 2.2 for the process split). |
| Database | **SQLite in WAL mode.** |
| Frontend | *(Amended by [ADR 11](11-preact-ui.md): Preact + htm for all UI, no Alpine.)* Django templates + **Alpine.js** (sender); plain **ES modules** (display, outbox, cache, crypto). No Node build, no React. Service workers and a web app manifest for both apps. Every asset is self-hosted (vendored Alpine, system fonts only). |
| Hosting | The desktop plus **Tailscale Funnel** (`*.ts.net` HTTPS). systemd **user** services. When the desktop is off, the server is unreachable. |
| i18n | **English and French from the start** (Amendment A2). The Django admin stays English. |
| Domain | User, Vault, Membership, Space (multiple controllers), Display, MemberDevice, Event (append-only log = history). |
| Events | Client-generated UUID, client `created_at`, type; server `received_at`. Accepted once per UUID (idempotent). Clients push; the server never pulls. MVP types: `content.posted`, `reaction.added`. |
| Offline | IndexedDB outbox; retry on open/foreground/`online` (iOS has no background sync); Android Background Sync is an optional extra. A display gets a snapshot on (re)connect, then live updates. |
| Media | A human-browsable folder `<MEDIA_ROOT>/<vault>/<space>/YYYY/MM/YYYY-MM-DD_HHMM_<shortid>.jpg` plus a sidecar `.json` (note, author, timestamps). Re-encoded, metadata stripped, served only through authorised views. |
| Security | Non-extractable ECDSA P-256 keys (WebCrypto) per device; challenge-response; short-lived session; no passwords in the public app; pairing codes claimed in admin; immediate revocation; authorisation derived only from the authenticated device; isolation tests on every endpoint and consumer. |
| Privacy | No analytics or third-party requests. Telemetry is last-seen plus app version only. Logs never contain note text or photo contents. |
| Code | Business rules as plain functions without side effects (time and IDs passed in), kept apart from Django/IO modules by convention (see Amendment A1). ruff for lint and format. Type hints throughout. |
| Workflow | Claude + runner + local model, coordinated through files (see `docs/workflow.md`). |

---

## 2. Recommendations on open choices

### 2.1 ASGI server: **uvicorn**

- The choice is `uvicorn[standard]` (uvloop, httptools, websockets). It is mature, fast, well supported by Channels, and simple to run under systemd.
- Daphne was considered. It is Channels' reference server, but it is slower and less widely used; we need nothing it alone provides.
- Hypercorn was considered for its multi-bind support. We don't need that, given 2.2.

### 2.2 Admin separation from Funnel: **two processes, admin absent from the public app** ⚑

The brief asks for "a single process with the in-memory channel layer" **and** "admin unreachable by construction". The two conflict: in the cleanest construction admin runs in its own process, and an in-memory layer can't carry a revocation from the admin process into the public process. The owner chose this resolution:

- **Public process:** `uvicorn coucou.asgi_public:application --host 127.0.0.1 --port 8000`. This is the **only** port given to `tailscale funnel`.
  - Settings: `coucou.settings.public_*` sets `ROOT_URLCONF = "coucou.urls_public"`.
  - That URLconf never imports `django.contrib.admin.site`, so no URL pattern for admin exists in this process.
  - The public process also leaves `django.contrib.admin` out of `INSTALLED_APPS`, and it has no password-auth views.
- **Admin process:** `uvicorn coucou.asgi_admin:application --host 127.0.0.1 --port 8001`. Plain HTTP on loopback; it is never Funnelled or served.
- **Tests that prove the construction:**
  - The public ASGI app returns 404 for `/admin/` and every admin path.
  - `coucou.urls_public` has no resolver that includes `admin.site.urls`.
- **Cross-process signalling (revocation and pairing claims):**
  - The public process runs one asyncio **DB watcher** that polls a small `auth_generation` counter every 1 s. A write from the admin process bumps the counter.
  - When the counter changes, the watcher loads the revoked or changed devices and closes their consumers through the in-memory group layer (`device.<id>` groups).
  - Every HTTP request and every inbound WebSocket message also re-validates the session row. A revoked device therefore can't act even between polls.
  - "Immediately" is defined as **≤ 2 s** to close sockets, and **0 s** to refuse new requests.
- Both processes share one SQLite file (WAL makes one writer plus concurrent readers fine at this scale).
- The in-memory channel layer stays **inside** the public process, which satisfies "single process" for everything real-time.

### 2.3 Session after challenge-response: **opaque server-side session cookie**

- On a successful challenge, the server creates a `DeviceSession` row.
  - token: `secrets.token_urlsafe(32)`, stored as a **SHA-256 hash** only
  - bound to the device
  - `expires_at` = now + **1 h**
- The cookie is `__Host-coucou_s` with `HttpOnly; Secure; SameSite=Strict; Path=/`, and no `Domain`.
- The client re-runs the challenge silently on 401. It needs no user interaction, because the key is on the device.
- Django's `contrib.sessions` and `contrib.auth` login are **not** used on the public app.
- **CSRF:** SameSite=Strict, plus a strict `Origin` check against the configured public origin on every unsafe method, plus a required `X-Coucou: 1` header (forces a CORS preflight for any cross-origin attempt).
- **WebSocket:**
  - authenticated by the same cookie at handshake
  - `Origin` must equal the public origin
  - the session is re-validated on every inbound message and by the watcher (2.2)
- **Revocation** deletes all of that device's sessions and bumps `auth_generation`.
- **Last seen:** a device's `last_seen_at` and `app_version` are updated at most once a minute.

### 2.4 Challenge and pairing protocol (owned by Claude; protected)

**Keys**
- Generated with `crypto.subtle.generateKey({name:"ECDSA", namedCurve:"P-256"}, false, ["sign","verify"])`.
- The `CryptoKey` objects are stored in IndexedDB; this uses structured clone and never exports the private key.
- The public key is exported as SPKI (DER, base64url) for registration.

**Challenge**
- `POST /api/auth/challenge {device_id}` returns a 32-byte random nonce: single-use, **60 s TTL**, bound to the device.
- The device signs `"coucou-auth-v1\n" + origin + "\n" + device_id + "\n" + nonce`, using ECDSA with SHA-256.

**Signature format**
- WebCrypto returns ECDSA signatures as raw `r‖s` (IEEE P1363, 64 bytes).
- The server converts them to DER with `cryptography`'s `encode_dss_signature` and verifies with `ec.ECDSA(hashes.SHA256())`.
- This conversion is the single most likely interoperability bug, so it has explicit tests with WebCrypto-generated vectors.

**Pairing**
- `POST /api/pair/register {public_key_spki, kind: "display"|"phone", app_version}` creates an **unpaired** `Device`.
  - The device gets a code of **8 Crockford-base32 characters (~40 bits)**, shown as `XXXX-XXXX`.
  - The code has a **10 min TTL** and works once.
  - The server keeps only the code's hash.
- **Rate limits:**
  - register: 5/min and 20/day per source IP; the IP is taken from Funnel's `X-Forwarded-For`, trusted only from loopback
  - pending cap: a global cap of **20** unpaired devices
  - expiry: unpaired registrations expire and are purged after 10 min
- **Fingerprint:** SHA-256 of the SPKI, first 80 bits, shown as `XXXX-XXXX-XXXX-XXXX` in Crockford base32, on both the device and admin.
- **Claiming:** in admin the owner enters the code, confirms the fingerprint, and assigns the device: a display to a Space, or a phone to a User.
- **Waiting for the claim:** the device polls `GET /api/pair/status`, authenticated by a signature over a fresh nonce, until it is claimed. It then runs the normal challenge.
- **Lost key:** the device simply registers again. The old record is revoked in admin.

### 2.5 Clock-skew rule (pure function) ⚑

Each request carries the client's current clock `sent_at`, and the server records `received_at`.

- **Skew:** `skew = received_at − sent_at` for that request.
- **Effective time:** `effective_at = min(client_created_at + skew, received_at)`.
  - Adding the skew corrects a device whose clock is consistently wrong, while keeping the true offline order of events created while the server was down.
  - Clamping to `received_at` ensures an event can never come from the future.
- **"Current content"** is the content event with the greatest `(effective_at, received_at, event_id)`. This is deterministic, and ties can't flip.
- All three timestamps are stored, and history is shown by `effective_at`.
- Lives in `coucou/ordering.py` and is unit-tested exhaustively.

### 2.6 Photo size and format limits: keep originals ⚑

The owner wants full-resolution originals kept, because storage on the desktop isn't a concern for now.

**Client:**
- The phone queues the **original file bytes** unchanged; it does no canvas resizing.
  - iOS Safari can't draw more than about 16.7 MP on a canvas, so a 48 MP iPhone photo can't be re-encoded on the device anyway.
  - iOS usually hands the page a JPEG when photos are picked through `<input type=file accept="image/*">`.
- A small canvas thumbnail is generated for the compose preview only.

**Server:**
- request body ≤ **40 MB** (configurable); note ≤ **280 characters**
- Pillow `verify()`, then re-open; decompression-bomb guard at **64 MP**, which covers 48 MP phone cameras
- accepted formats: JPEG, PNG, WebP, **HEIC/HEIF** (adds the `pillow-heif` dependency for files that Safari passes through unconverted)
- **Every** stored file is a fresh re-encode with no EXIF, XMP, GPS or maker notes. Orientation is applied first with `exif_transpose`, and the ICC profile is kept only when it's sRGB/Display P3, so colours stay right.
- Two files are written per photo:
  1. **Original:** full resolution, JPEG **q95**, written to the history folder (the file you browse).
  2. **Display copy:** long edge ≤ **3072 px**, JPEG q85, written to a derived cache (`<MEDIA_ROOT>/.display/…`). It is regenerated from the original if missing, and it's what displays and phones download.
- The uploaded bytes themselves (with metadata) never touch disk. They are processed in memory or in a temporary file that is deleted afterwards.

### 2.7 Reaction set

- Each space has a configurable ordered list of **3–5** emoji, validated by a plain function.
- The default is **❤️ 😂 😮 🥰**.
- Emoji render with each device's system emoji font; no emoji web font is bundled.

### 2.8 Integration tests and the database ⚑

The brief says integration tests fake external dependencies. Faking the database for **isolation tests** would prove nothing, though, because vault scoping lives in real queries. Proposal:

- **Unit tests** (`tests/unit/`) cover plain functions without side effects: fast, no Django, one test file per module (see Amendment A1).
- **Integration tests** (`tests/integration/`) fall into two kinds:
  1. **Service tests.** Edge services are wired to **in-memory fakes** of repository Protocols (`EventRepo`, `DeviceRepo` …) and of the clock, ID source and media store, which lets orchestration be tested without the ORM.
  2. **Django tests.** Views, consumers, ORM repositories and **all isolation tests** run against Django's in-memory **test SQLite**, treated as an in-process dependency, not an external one.
  - In both kinds, the clock, randomness and network are always faked, and media goes to a tmp dir.
  - The ORM repositories also pass the **same contract tests** as the fakes, so the fakes can't drift.
- **End-to-end tests** (`tests/e2e/`) run against **staging**: real uvicorn, a real SQLite file and media under `var/staging/`, and real WebSockets.

### 2.9 Browser end-to-end tests: **yes, a small set**

- The tool is **pytest-playwright** via uv (a dev dependency; browsers downloaded once, never at runtime). It covers the JavaScript that no Python test can reach: WebCrypto, IndexedDB outbox and service worker.
- It runs **Chromium** (Android proxy) and **WebKit** (a rough stand-in for iOS Safari, *not* a substitute).
- The initial flows:
  1. pair a display and a phone
  2. post → display updates
  3. react → sender sees it
  4. go offline, queue, come back, deliver
- A **manual real-device checklist** (Android + iPhone) stays part of each milestone sign-off.

### 2.10 Type-checker gate: **mypy, strict**

- **mypy** with `django-stubs`, as a runner gate.
- `strict = true` for the whole `coucou` package (migrations excluded); tests are checked less strictly.
- Pyright/ty were considered. `django-stubs` support makes mypy the pragmatic choice.

### 2.11 SQLite configuration

- The database settings use `OPTIONS = {"init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;", "transaction_mode": "IMMEDIATE"}`, which Django 5.1+ supports.
- Each environment has its own file: `var/dev/`, `var/staging/`, `var/prod/`.

### 2.12 Settings and environments

- The settings modules are `coucou/settings/{base,dev,staging,prod}.py`, with each environment's public and admin variants.
- Secrets come from an uncommitted `.env` file (`var/<env>/.env`, or the path in `COUCOU_ENV_FILE`). A committed `.env.example` documents the keys.
- The public origin is configured explicitly (`COUCOU_PUBLIC_ORIGIN`) and used by Origin checks and the signed challenge.

### 2.13 Headless Claude from the runner

- The runner calls `claude -p` with:
  - `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` **removed** from the environment, so the Pro login is always used
  - an explicit per-job `--allowedTools` list and `--permission-mode`
  - `--output-format json`, `--permission-mode dontAsk` (anything outside the allowed tools is denied) and a wall-clock timeout; this CLI version has no turn cap
- Usage-limit responses are detected. The runner sleeps until the parsed reset time (fallback: exponential backoff from 15 min, max 5 h) and resumes. It never loops tightly.

### 2.14 Local model invocation

- The runner calls `opencode run` with:
  - the project `opencode.json` (model `lmstudio/qwen/qwen3.6-35b-a3b`)
  - `--title`, so no extra LLM title call is made
  - the task file attached
- The runner **never changes LM Studio's model settings.** Before each OpenCode call, it sends one sequential warm-up request so that JIT loading happens once, with the owner's settings. ~~It also checks LM Studio's `loaded_context_length` against `limit.context` in `opencode.json` and warns on mismatch.~~ Replaced by A3.
- **Interactive questions are denied** (`permission.question: "deny"`). Questions go through the BLOCKED protocol.

---

## 3. Consequences

- Two processes means two systemd units plus one for Funnel. Revocation is "≤ 2 s" rather than instant for already-open sockets.
- The test layers are explicit: faked repositories where they add value, and the real test SQLite where the question is "does the query scope correctly".
- Playwright adds a dev-only download of about 300 MB of browsers.
- Keeping originals means large uploads (up to 40 MB) sit in the phone's outbox until delivered, and adds `pillow-heif`. The history folder grows by roughly 3–8 MB per photo.
- Phones need HTTPS for WebCrypto, service workers and Wake Lock. Real-device testing from M2 needs Tailscale (`tailscale serve` on the tailnet, or Funnel).

## 4. Owner review

Resolved in review on 2026-09-27:
- 2.2 process split: chosen by the owner.
- 2.3 session TTL: 1 h confirmed.
- 2.5 clock-skew rule: accepted.
- 2.6 photos: keep full-resolution originals, display copies at 3072 px.
- 2.7 default reactions: ❤️ 😂 😮 🥰 confirmed.
- 2.8 test SQLite for isolation tests: accepted.
- 2.9 Playwright and 2.10 mypy gate: kept.
- Logo direction: D (bird in the round window), to be refined for the icons in M3–M4.

## Amendments

### A1 (2026-09-27, owner-directed): one flat Django app, purity by convention

- **Layout:** there are no `core/` or `edges/` packages, no `logic/` folders and no per-feature Django apps. The project has **one Django app, `coucou`**, with one `migrations/` folder.
  - Models and admin are small packages split by topic (`coucou/models/{accounts,spaces,events,devices}.py`, and `coucou/admin/` to match), so device code can be a protected path of its own.
  - Other modules sit flat in `coucou/`.
- **Purity is a convention, not a gate.** Business rules are written as plain functions with time and IDs passed in (e.g. `coucou/ordering.py`), which keeps them easy to unit test. Modules aren't marked, and **import-linter is not used**. Reviews catch drift.
- **Admin separation** is enforced by an ordinary test (see 2.2), not by an import contract.
- **Unit tests:** **one unit test file per module.** `coucou/<name>.py` → `tests/unit/test_<name>.py`, never two for the same module. The runner's `layout` gate checks this by file name only.
- **mypy:** strict across the whole `coucou` package.

### A2 (2026-09-27, owner-directed): English and French from the start

Replaces the brief's "English only for the MVP". Mum reads French, so both languages ship together.

- **Languages:** `LANGUAGES = en, fr`; the source language is English. **The Django admin stays English**: the admin process has no `LocaleMiddleware`, so it always uses `LANGUAGE_CODE = "en"`, and admin-only labels are plain strings, not wrapped for translation.
- **Who sees which language:**
  - **phones** follow the person's `User.language`
  - **displays** follow `Device.language`, set in admin (e.g. Mum's kitchen display in French)
  - **before a device is paired** (pairing screens), the browser's `Accept-Language` decides, via `LocaleMiddleware`
  - M2 adds a small middleware that activates the authenticated device's language
- **Server-side strings:** wrapped with `gettext`/`{% translate %}`, in `coucou/locale/fr/LC_MESSAGES/django.po`.
- **Client strings:**
  - JS strings use Django's built-in `JavaScriptCatalog` view (`djangojs.po`), served from the public app and cached by the service worker, so French still works offline
  - dates and times use `Intl.DateTimeFormat` with the active language
- **API errors** carry a stable `code` (e.g. `note_too_long`); clients show translated text for the code. Server messages are for logs and tests only.
- **What isn't translated:** user content (notes), emoji, file names and the history folder.
- **Enforcement:**
  - the runner's `translations` gate regenerates the catalogues, fails on any missing or fuzzy French translation, then restores the files
  - a test checks that the committed catalogues are complete and their `.mo` files are compiled and up to date
  - compiled `.mo` files are committed, so deploys need no gettext tools
- **Authoring:** a task that adds user-facing strings lists `coucou/locale/fr/LC_MESSAGES/*.po` and `*.mo` in its `files:` and writes the French translations itself. Claude checks the French at milestone review.

### A3 (2026-09-28, owner-directed): the model's context length lives only in LM Studio

The owner sets the context length in LM Studio and changes it as they see fit (157,440 at M0, 183,808 from M1). The repo doesn't restate it.

- `opencode.json` has no `limit` for the local model.
- The runner no longer compares the two. It records the context LM Studio actually loaded in the session report, as information only.

### A4 (2026-09-28, owner-directed): every commit says who made it

The owner wants to see which commits the local agents made. Until now the runner's squash-merges named the local model only in the message body, under the owner's git identity, and runner and headless-Claude commits looked like the owner's own.

- **Local-model merges** are authored by `Coucou local model <local-model@coucou.invalid>`; the committer stays the owner. They end with the trailers `Agent: local-model`, `Task: <id>`, `Model: <LM Studio key>` and `Attempts: <n>`. WIP commits on task branches carry the same author.
- **Runner bookkeeping** (task moves, session reports, review metrics) is authored by `Coucou runner <runner@coucou.invalid>`, with `Agent: runner`.
- **Headless Claude** (escalations, reviews) commits carry `Agent: claude-headless`; **interactive Claude** commits carry `Co-Authored-By: Claude …`. Owner commits carry nothing.
- **Listing:** `uv run runner commits --milestone N` lists the local-model commits since `mN-start` (sha, task, attempts, lines changed). Commits from before A4 are recognised by their body text; history isn't rewritten.
- **Reports:** the session report shows each merged task's commit, and `docs/reviews/mN.md` includes the listing.

### A5 (2026-09-28, owner-directed): the pairing screen has a language switch

Before pairing, the browser's `Accept-Language` decides the language (A2). A French speaker using a tablet set to English would then get instructions they can't read.

- The pairing screen at `/` shows **English | Français**, each named in its own language.
- Choosing one sets Django's language cookie for a year and reloads the page. `LocaleMiddleware` prefers that cookie to `Accept-Language`, which stays the fallback.
- After pairing, nothing changes: a display follows the language set when it was claimed, and a phone its person's.
