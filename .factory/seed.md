# Original brief (reference only)

> Kept verbatim for reference. Once ADR 00 is Accepted, **ADR 00 and the docs are the source of truth**; where they differ from this brief, they win.

---

# Setup brief: Coucou

You are Claude Code, running on my Claude Pro subscription in an empty project folder on my Linux desktop. This brief covers two things:

1. the product I want to build
2. the frontier + local-model workflow we'll use to build it

Read all of it before doing anything. Your first deliverable is **not code**. It's a set of drafts for my approval (see "Your first steps" at the end).

If anything here is contradictory, ambiguous or looks like a bad idea, say so. Ask all your questions in one batch rather than guessing.

---

## 1. The product

### Purpose

A privacy-first "ambient presence" system. A person sends small moments (a photo and/or short note) to always-on displays in other people's homes. Recipients notice that "something changed" while walking past and can tap to react. It must feel like a calm ambient object, **not** a chat app, social feed or smart-home dashboard.

### Name and identity

The project is called **Coucou**. It's the casual French "hi / peek-a-boo, thinking of you", chosen because it's instantly warm for my French Mum and easy for English speakers.
- Use `coucou` as the slug for the repo, the Python package and the Django project.
- "Vault" stays as the internal term for the privacy boundary. It isn't user-facing branding.
- Wherever the app shows text to users, the tone should be light and warm, never corporate.
- **English only for the MVP**, but keep user-facing strings translatable (Django i18n), since French is a likely early addition.

**Logo:** something cute, simple and calm that works as a small app icon and favicon. Two directions to explore:
- a little bird peeking out of a small window
- two "o"s as eyes peeking over a line

### First real use

- One vault, **me + my Mum**.
- One space, called "Us", with **two displays**: one in my home, one in hers.
- Both displays always show the same content, because it's one space.
- We are **both senders** on that space. At first it may be only me.
- Reactions record which display they came from. A tap on Mum's display is visible to me, and the other way round.
- **Soon after:** my sister joins, possibly in a new vault (Mum + sister + me). She uses an **iPhone**, so everything must work in iOS Safari from the start. Mum and I use Android.

### Domain model

- **User:** a person. Created by me in Django admin; there is no public sign-up.
- **Vault:** the privacy and security boundary; a group of members. Every authorisation decision is scoped to a vault.
- **Space:** belongs to exactly one vault. It is the shared experience, meaning its current content plus its history. A space can have **multiple controllers** (members allowed to post). Other members can react.
- **Display:** a device that renders exactly one space. A space can have many displays.
- **Member device:** a user's phone, paired to that user and used to post and view reactions.
- **Event:** anything that happens (content posted, reaction added). The event log is the source of truth and is also the history.

### Changes from my earlier notes

My older notes may still exist, but these decisions replace them:

- Device authentication uses **asymmetric keys**, not a shared HMAC secret. See section 3.
- Spaces can have **multiple controllers**, not a single owner.
- Hosting is **my desktop plus Tailscale Funnel**, not a VPS.
- There is **no native Android app** in the MVP. Everything is a web app / PWA.
- Mum **sends** as well as reacts.

---

## 2. Architecture decisions (already made)

- **Language and tooling:** Python, managed with **uv** for everything: environments, dependencies, running tools.
- **Framework:** **Django**, using Django admin for all setup and management in the MVP.
- **Real-time updates:** Django **Channels** (WebSockets) on an ASGI server. Propose which server in ADR 00. Use a single process and the in-memory channel layer for now.
- **Database:** **SQLite** in WAL mode.
- **Frontend:**
  - Django templates plus **Alpine.js** for sender screens; plain JavaScript ES modules for the display, outbox and caching logic
  - **no Node build step and no React**
  - **service workers and a web app manifest**, so both apps can be installed to the home screen and load when the server is unreachable
  - all static assets **self-hosted**: no CDNs, no third-party fonts, no requests to anyone but our server
- **Hosting:**
  - the server runs on my Linux desktop, exposed to the internet **only** through Tailscale Funnel (free plan, stable `*.ts.net` HTTPS address)
  - systemd user services start the server and Funnel when the machine comes up
  - when my machine is off, the server is simply unreachable, and clients must cope with that
- **Django admin** is for me only, on localhost. It must be **unreachable through Funnel by construction**, not just by a config check. For example, serve admin on a separate port bound to 127.0.0.1 and only Funnel the public app port. Propose the mechanism in ADR 00.

### Offline-first event model

- **Every client action is an event.** It carries a client-generated UUID, the client's creation time and a type. The server records when it received it.
- **The server accepts each event once**, keyed by its UUID, so client retries are always safe.
- **Clients keep an outbox** in IndexedDB and retry until the server is reachable. They show a quiet "waiting to deliver" state. When the server comes back, clients **push** to it; the server never pulls.
- **iOS home-screen web apps don't support background sync.** Delivery must work by retrying when the app is opened or brought back to the foreground. Background sync on Android is an optional extra.
- **On (re)connect, a display gets a snapshot** of its space's current state, then live updates.
- **Current content:** the latest content event by client creation time wins, and every event is kept in history. Client clocks can be wrong, so propose clock-skew handling in ADR 00.
- **MVP event types:** content posted (photo and/or note), reaction added.

### Media and the history folder

Photos live on disk in a **human-browsable folder**, so I can look through them offline with a file manager:
- path pattern like `<MEDIA_ROOT>/<vault-slug>/<space-slug>/YYYY/MM/YYYY-MM-DD_HHMM_<shortid>.jpg`
- a small sidecar file next to each photo with the note, author and timestamps
- `MEDIA_ROOT` configurable

Each upload is:
- limited in size
- validated as a real image
- **re-encoded, with all EXIF data (especially location) removed**
- served **only through authorised views**, never as public static files

An in-app history view is on the roadmap. It will be built on these same files and events.

### UI intent

- **Display:**
  - full screen and calm: photo, note, a few reaction emoji (a configurable set of 3–5)
  - gentle transitions
  - keeps the screen awake (Wake Lock API where available)
  - no navigation and nothing else to tap
  - first tested in a browser on my Android phone
- **Sender app:**
  - mobile first
  - compose a photo (camera or gallery) and/or a note, preview it, send it
  - see delivery status and recent reactions
  - must be simple enough for my Mum

---

## 3. Security baseline

The public surface is **only** what displays and member phones need. Everything else is on localhost.

- **No public sign-up.** Users, vaults, spaces and device assignments are created in admin by me.
- **Device identity:**
  - every display and every member phone generates a **non-extractable ECDSA P-256 key pair** with WebCrypto, stored in IndexedDB
  - the server stores only the public key and verifies with the `cryptography` library
  - authentication is a challenge-response using a server nonce that is single-use and short-lived
  - after that, the client gets a short-lived session: HttpOnly, Secure, SameSite=Strict cookies or equivalent
  - there are **no passwords in the public app at all**
  - use standard libraries only and invent no cryptography
- **Pairing:**
  - a new device registers its public key in an unpaired state and shows a short pairing code
  - the code expires after about 10 minutes, works once, has enough entropy and is rate-limited
  - I claim the code in admin and assign the device: a display to a space, or a phone to a user
  - a short key fingerprint is shown on both the device and in admin, so I can confirm they match
  - unpaired registrations are rate-limited and expire
  - if a device loses its key (for example, iOS clears storage), it simply re-pairs
- **Revocation:** revoking a device in admin cuts it off immediately, including its open WebSockets.
- **Authorisation:**
  - always derive what a caller may access from the **authenticated device**: display → space, or phone → user → memberships
  - never trust client-supplied IDs for access decisions
  - a display can **only** read its space and add reactions
  - a phone can only post to spaces its user controls, and read what its user may see
- **Isolation tests:** every endpoint and WebSocket consumer gets tests proving that a device or user from one vault cannot read or write another vault's data.
- **Privacy:**
  - no analytics, tracking, ad IDs or third-party requests
  - minimal telemetry: last seen and app version only
  - logs never contain note text or photo contents
- **Secrets:** SECRET_KEY and similar come from an uncommitted env file. `.gitignore` covers the database, media, `var/` and env files.

---

## 4. MVP scope and milestones

**"Working" means:**
1. I post a photo and note from my phone to "Us".
2. Both displays update within seconds.
3. Mum taps a reaction, and I see it in my sender app.
4. Everything survives reboots, network drops and my desktop being off: clients queue actions and show the last content, then catch up when the server returns.

**Milestones:**

0. **Foundations (Claude only).**
   - uv project, Django, settings for dev, staging and local-production, the core/edges structure and the event model
   - authorisation helpers with isolation tests
   - all gates, the runner, the OpenCode config, and systemd unit templates (don't install system services without asking me)
1. **Admin setup:** models registered and usable in admin, plus seed or management commands where helpful.
2. **Device pairing and authentication** for displays and phones. *Protocol, server and client crypto are Claude only.* The local model may build the pairing-screen UI.
3. **Display app:**
   - WebSocket live updates and the snapshot on reconnect
   - offline cache of the last content and the app shell
   - reaction outbox
4. **Sender app:** compose, offline outbox including photo blobs, delivery status. Works for me and Mum, and in iOS Safari.
5. **Reactions for senders, and the history folder:** reactions visible in the sender app; the media and sidecar folder layout finished.
6. **Pilot:**
   - systemd services and Funnel, with the admin separation verified
   - end-to-end tests on staging
   - a checklist for setting up a display on an Android device

### Roadmap (not MVP; keep it in `docs/roadmap.md`)

- in-app history and timeline
- "thinking of you" pulse (a content-free glow on the display)
- "seen" signal (gentle, no read receipts)
- scheduled moments
- night dimming
- "on this day" resurfacing of old photos
- in-app and push notifications
- invitations and self-service vault management
- sister's vault
- text replies
- native Android kiosk wrapper: lock task, start on boot, Android Keystore
- end-to-end encryption
- always-on hosting: a container image for a VPS or free cloud host
- backups and a retention policy

---

## 5. Code and testing rules

**Functional core, imperative shell:**
- business logic lives in a `core` package of **pure functions**: no Django, no database, no files, no network, no reading the clock or randomness (time and IDs are passed in)
- everything with side effects lives at the edges
- an **import-linter** contract enforces this

**Tests:**
- **Unit tests** cover pure functions only.
- **Integration tests** exercise the edges together with the core, with external dependencies mocked or faked. The Django ORM makes mocking the database awkward. Propose an approach in ADR 00 (for example, repository interfaces with in-memory fakes) rather than quietly deviating from this rule.
- **End-to-end tests** run against a **staging** environment with its own settings, SQLite file and media folder under `var/staging/`, using the real database, files and WebSockets. Propose whether browser-level end-to-end tests (e.g. Playwright via uv) are worth it for the MVP.

**Quality:**
- ruff for linting and formatting
- type hints throughout; propose in ADR 00 whether a type checker becomes a gate

---

## 6. Documentation rules

- **`README.md`:** high level and light: what this is, how to run it, pointers into `docs/`.
- **`AGENTS.md`:** a **short** list of rules shared by you and the local model (aim for about 40 lines). No duplication of the README or docs; link to `docs/*.md` instead. Suggested contents:
  - stay inside the task's allowed files
  - core/edges purity
  - the testing rules
  - never edit protected paths or existing tests
  - no new dependencies without an explicit task
  - no third-party network calls
  - the BLOCKED protocol
  - the discoveries inbox
  - never build against an ADR that isn't Accepted
  - which docs to read for which kind of work
- **`CLAUDE.md`:** **Claude-only** duties, with no duplication of AGENTS.md or the README:
  - planning and task-writing
  - owning the protected paths
  - handling escalations
  - running the review loop
  - drafting ADRs
  - improving the workflow (section 8)
- **`docs/`:** topic docs read on demand, e.g. `architecture.md`, `security.md`, `testing.md`, `workflow.md`, `task-format.md`, `roadmap.md`, `backlog.md`, and `reviews/`.
- **`docs/adr/`:** Architecture Decision Records.
  - `00-initial.md` first; later ones are `01-<slug>.md`, `02-<slug>.md` and so on
  - status is Proposed, Accepted or Superseded
  - **only I can mark an ADR Accepted**
  - you draft ADRs; the local model never writes them
- **Keep this brief** as `docs/original-brief.md` for reference. Once ADR 00 is accepted, ADR 00 and the docs are the source of truth.

---

## 7. The build workflow

### Roles

- **Me:**
  - approve ADRs and workflow changes
  - sign off each milestone after trying it on real devices
- **You (Claude Code, Pro login):**
  - architect and planner
  - the only implementer of protected paths
  - escalation handler and reviewer
- **The runner:** a deterministic Python script (`uv run runner`) with **no AI in it**. It picks tasks, calls the local model, runs the gates, merges, retries and escalates, and calls you headlessly at defined points.
- **The local executor:** OpenCode (headless) using my local Qwen model through LM Studio. It implements one small task at a time.

**Everything is coordinated through files in the repo.** Nothing passes directly between you and the local model.

### Local environment facts

- **Machine:** Linux, 8 GB VRAM, 64 GB RAM.
- **Model:** LM Studio serves a Qwen ~35B-A3B MoE model on `http://localhost:1234`, with the context set to **64k**. It can go higher, but quality and speed drop. Ask me for the exact model ID, or read it from `http://localhost:1234/v1/models`.
- **OpenCode:** already installed and used with this model. Create a project-level OpenCode config pointing at LM Studio's OpenAI-compatible endpoint (`/v1`).
- **Check the CLIs rather than guessing:** verify the real flags with `opencode run --help` and `claude --help`, and the docs if needed.
- **Claude runs must use my Pro subscription:**
  - when the runner starts `claude -p` headlessly, it must **strip** `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` from the subprocess environment, so it always uses my Pro login and never API billing or LM Studio
  - restrict headless Claude's tools and permissions to what each job needs
  - if a Pro usage limit is hit, the runner **pauses and resumes after the reset** rather than failing or retrying in a tight loop

### Task files

- **Location:** tasks live in `tasks/ready/`, `tasks/done/` and `tasks/escalated/`.
- **Frontmatter:** YAML with:
  - id and milestone
  - `depends_on`
  - allowed `files`
  - the `tests` that define done
  - `max_diff` (about 150 lines by default)
  - an optional `finding` ID for review fixes
- **Sections:**
  - **Goal**
  - **Context:** the exact signatures and types needed, pasted in, so the model never has to explore
  - **Pattern to follow:** one existing file
  - **Steps:** specific down to function names
  - **Done when**
- **Size:** 1–3 files and one concept per task.
- **Skeleton-first:** you write the signatures and stubs and the **failing tests** first. The local model makes them pass.

Document the full format in `docs/task-format.md`.

### Runner loop (per task)

1. Pick the next task in `ready/` whose dependencies are done.
2. Create a task branch from main.
3. **Pre-flight:** check that the files and symbols in the Context section exist as described. If not, escalate immediately.
4. Run OpenCode headlessly with the task file (it reads AGENTS.md).
5. **Gates:**
   - the task's tests, then all unit and integration tests
   - ruff
   - the import-linter purity contract
   - only allowed files changed
   - **protected paths untouched**
   - **existing test files unchanged** (hash check)
   - diff under `max_diff`
   - no new dependencies
6. **Pass:** merge to main and move the task to `done/`.
7. **Fail:**
   - attempt 2: the same context plus the exact gate output
   - attempt 3: reset the branch, start with a fresh context, and include the previous failure as a warning
   - still failing: move to `escalated/` with the logs and last diff, pause any dependent tasks, and continue with independent ones
8. **BLOCKED:** if the local model writes `BLOCKED.md`, escalate immediately. The file names one category:
   - the spec's assumption is false
   - the task needs a file outside the allowed list
   - it needs information
   - it found an unrelated problem but is not blocked (this one continues)
9. **Discoveries:** unplanned work the local model notices goes into `docs/discoveries.md`, never into the code.

Run logs go to `var/runs/` (gitignored).

**Protected paths** are listed in one config file. Initially they cover:
- the device authentication protocol (server and client JavaScript)
- pairing
- authorisation and query scoping
- session and cookie settings
- admin exposure and separation
- upload handling and media serving
- WebSocket authentication and routing
- deployment, Funnel, systemd and secrets
- migrations that change the security model
- the runner and gates themselves

### Automated escalation and review loop (bounded; no human needed for a few rounds)

**Escalations.** The runner can call you headlessly on escalated tasks. You usually repair or split the spec and put it back in `ready/`. You do the task yourself if it's genuinely hard or protected.

**Review.** When all of a milestone's tasks are merged and the end-to-end tests pass on staging, the runner starts a headless review of the milestone diff. You grade each finding:
- **Blocking:** bugs, security issues, violations of AGENTS.md or an ADR.
- **Should fix:** design drift, missing edge cases, weak tests.
- **Nit:** style and polish. Nits **never loop**; they go to `docs/backlog.md`.

**Routing each blocking or should-fix finding:**
- a small, clear finding becomes a fix task for the local model, tagged with the finding's ID
- a finding that is protected, or quicker to fix than to specify, you fix directly
- a finding that needs a design decision becomes a draft ADR, and **the loop stops for me**

**Re-review** covers only the fix diffs and whether each finding is resolved. There's no fresh full re-read. New blocking issues found in the fixes count; new should-fix points about untouched code go to the backlog.

**Stop rules:**
- at most **3 review rounds** per milestone
- a finding that comes back a second time isn't sent to the local model again; you fix it. A third time stops the loop
- the loop stops if a round's number of findings isn't lower than the previous round's
- the loop stops immediately for:
  - an ADR that needs approval
  - a security finding you can't resolve confidently
  - a change the plan didn't foresee that affects other milestones
- a cap of about **10 headless Claude runs per milestone**, covering reviews and escalations. Make this configurable

**Milestone report** in `docs/reviews/mN.md`:
- what was built
- findings and how each was resolved
- what went to the backlog
- metrics: tasks, attempts per task, escalation rate, review rounds, headless Claude runs
- why the loop stopped, if it stopped early

**Only I can mark a milestone done.**

---

## 8. Improving the workflow

The workflow itself can be improved over time: the runner, gates, caps, task format, AGENTS.md rules and review-loop rules. When metrics or experience suggest a change, propose it the same way as an architectural decision: **as an ADR for my approval**, with the evidence from milestone reports. Don't change workflow rules, gates or caps without an accepted ADR. Bug fixes to the runner that don't change behaviour are fine. Mention workflow observations briefly in milestone reports even when you're not proposing a change.

---

## 9. Your first steps

1. **Read and question.**
   - read this brief
   - ask me one batch of clarifying questions if anything is unclear or contradictory
   - list any assumptions you're making
2. **Check the environment.** Check for, and report on: `uv`, `git`, `claude`, `opencode`, `tailscale`, and the LM Studio server with its models endpoint. Don't install system packages or services without asking.
3. **Draft for approval. No application code yet.** Draft:
   - `docs/adr/00-initial.md`: the decisions above, plus your recommendations on the open choices:
     - ASGI server
     - how admin is separated from Funnel
     - how integration tests fake the database and other edges
     - whether to use browser end-to-end tests
     - type-checker gate
     - clock-skew rule
     - session mechanism after challenge-response
     - photo size and format limits
     - reaction set
   - `README.md`, `AGENTS.md` and `CLAUDE.md`
   - the `docs/` topic files and the protected-paths list
   - the milestone 0 plan

   Also draft **2–3 SVG logo concepts** for Coucou in `docs/brand/`, along the directions in section 1. I'll review them with you. Once I pick one, it becomes the favicon and the PWA icons in milestones 3–4.

   Initialise git and commit the drafts. Then **stop and wait for my approval**.
4. **After I accept ADR 00:** build milestone 0 yourself, including the runner and gates. Then write `docs/reviews/m0.md` and stop for my sign-off.
5. **Calibrate.** Before starting milestone 1 for real, run the pipeline end to end with one or two small milestone 1 tasks for the local model. Report how it went (attempts, gate failures, timing), plus any task-size or context adjustments you'd suggest.
