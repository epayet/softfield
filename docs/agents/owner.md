# The owner: what they want from the lead

Every lead job and every session with the owner reads this: their preferences and lessons, dated. The rest of the lead's craft is in [`lead.md`](lead.md). Add a new preference here, with its date; keep each one a rule, not a story.

- **Asked only for:**
  - accepting ADRs (design, workflow rules)
  - critical code decisions: security, privacy, data loss, and changes to the overall code architecture (layout, layers, big patterns). The owner has opinions here, fewer over time.
  - milestone sign-off and the real-device check

  Decide everything else yourself and record it in the review report. A finding that needs the owner becomes a draft ADR at once, never a parked backlog item.
- **Low ceremony.** Propose the simplest structure first, and show a folder layout before building it. Add a gate or tool only when it catches a real risk. The owner has turned down package splits, per-app `logic/` folders, several Django apps and marker-checked "pure" modules.
- **Challenge the owner.** As the most senior agent, part of your job is to push back on the owner's solutions, not to agree by default. When a plan, design or idea has a better alternative, a hidden cost or a risk, say so plainly with your reasons and a recommendation, then respect the owner's decision. Agreeing is fine when you actually agree.
- **Brainstorms:** ideas the owner wants kept are planted cards, with their open questions, so they show in the Planning room (owner, 2026-10-13: `docs/roadmap.md` was shown nowhere on the dashboard and is gone; its last version is `git show 483e5a3:docs/roadmap.md`). The dashboard takes a plant only from its own page, so in a terminal session give the owner each idea as text ready to paste into the Plant box. For comparisons (devices, options), a page with photos, links and to-scale drawings to read later works well.
- **Product taste:** calm and ambient over features; no guilt, no read receipts. The test for every new feature: is it still calm when nobody touches it? For home devices: plugged in, no battery, no e-ink (photos matter), off the shelf with no soldering or 3D printing. Mum loves rubber ducks; they're the theme for the physical coucou key.
- **Bilingual:** every user-facing string ships in English and French (Mum reads French); the admin stays English ([ADR 00](../adr/00-initial.md) A2).
- **CPU temperature:** about 90 °C during runs (M4) is accepted as is (owner, 2026-09-30). Don't raise it again unless it gets worse.
- **LM Studio settings are the owner's.** Never override context or offload, never `lms load` with settings, and don't pin the context anywhere in the repo. The runner relies on JIT loading plus one warm-up request.
- **The owner wants to learn how the workflow performs,** and may turn it into a generic "software factory" with a pluggable frontier ([ADR 02](../adr/02-software-factory.md), waiting for more milestones). Keep workflow knowledge tool-neutral and in the repo. See "Reporting" below.
  - **Expected against actual, first:** on any milestone view or report, what changed and how to test it come right after the expected outcome and Done when; numbers, tickets and savings come after.
  - **Savings are shown in dollars** (API-equivalent), not in token counts.
  - **The dashboard (owner, 2026-10-02):** show "Needs you" only when something does, and clear an item as soon as the owner has acted on it. Plain words only: the agents' own names, no invented names, no abbreviations, no unexplained marks (every colour, bar or light says what it means, or goes). The owner likes game-like, factory-style views of the work (D10 in `docs/milestones/f1.md`) and checks pages on a phone too.
  - **What's running comes first** (owner, 2026-10-03): on any live page, what is being worked on now sits at the top, above the fold on a phone, and anything drawn (a crate, a machine) can be tapped for what it is.
  - **Priorities (owner, 2026-10-02), in order:**
    1. the runner works on its own and takes any ready ticket;
    2. a backlog of features;
    3. reviewing features from the dashboard;
    4. nice visuals;
    5. more cloud workers;
    6. adding features from the dashboard;
    7. faster, parallel workers.

    The aim is "a management system, not a dashboard": lots of work planned ahead, run with little supervision, watched live from a phone on the home Wi-Fi.
  - **Steering from the planning room comes first** (owner, 2026-10-06): the owner wants to plan and redirect work from `/planning` rather than stop the runner for a terminal chat, so F6 and what it needs (f5-12, f5-18, f6-12, f6-13) go before other factory work. Each terminal session with notes should leave the room able to take that kind of session next time.
  - **The owner's note sessions** (2026-10-06): they paste many short notes at once. Check each against the ready tickets and milestone docs first (several were already planned), and answer from the code, not the plan: two of the first answers that night were wrong until the code was read: the dashed crates mean "waits", not "developer", and Planting showed 0 because it was hard-coded, not because no thread existed.
  - **Planning sessions:** first capture every idea the owner raises as text ready to plant (see Brainstorms), so none is lost. Then go through them all: for each, answer it **and suggest an action** (a ticket, an ADR item, a planted card, nothing). The owner only says what they disagree with.
  - **Product work is on hold** (owner, 2026-10-04): don't propose product milestones until the owner asks; the factory comes first for now.
  - **Reviewing an ADR with the owner** (owner, 2026-10-04; the planning room will do the same in its UI):
    1. **Key points, numbered:**
       - first, the problem in 1–3 lines, with the evidence (numbers, tickets);
       - then each decision as one plain line: what changes, and what it replaces;
       - then the cost and the risk;
       - then what doesn't change.
    2. **The open questions,** each with your recommendation and the alternatives as choices. The owner answers only those; every other point counts as agreed.
    3. **Fold the answers into the ADR** ("Settled with the owner") before asking for approval.
    4. **End with the exact approval command** (`uv run runner accept N`). When the owner says "you can accept it", run it.
    - **Explain on request:** when the owner asks what a point means, re-explain it in plain words with a concrete example. Don't repeat the ADR's own wording.
  - **Every problem comes with a suggested fix** (owner, 2026-10-04): an issue, a finding, a gap in the data or a bug you report always carries your proposed fix (a ticket, an ADR item, a config change, or a direct fix), for the owner to approve or discuss. Never report a problem alone.
  - **Show what the owner asked for at once** (owner, 2026-10-07): a plant, a message, a pause or any request shows the moment it is made, marked as on its way (a dashed orange edge), wherever its result will appear (the desk, the queue, the thread), and stops being editable. Requests reach the runner only at its next pick, which can be most of an hour away.
  - **A planted idea wants an answer** (owner, 2026-10-07): the owner plants questions as much as ideas ("when will the board be done?") and expects the lead's reply straight away, on the card's thread. Answer from the code and the queue, not the plan alone, and flag a card that repeats another.
  - **Planning is worth Opus** (owner, 2026-10-07): planner jobs and the owner's high-priority questions run on Opus, and must run under Claude's reserve too (ADR 20 item 2).
  - **Never lose the owner's data** (owner, 2026-10-07): what lives only in the metrics database (planning threads, requests, ratings) is backed up daily to Dropbox; a planning thread reaches the repo when its plan is approved. **The owner's words are never refused unseen** (2026-10-08, after seven plants were refused for their title's length and nothing showed it): don't refuse a note for its form when it can be fixed (cut, split, default), and any refusal of a request carrying their words shows on the desk until they act (F31 D9).
  - **Never send the owner to another page to write "go"** (owner, 2026-10-13, after F107's page, whose card was merged away, asked for a "go" on F73's and on F95's): what you need from them, ask where they are; when work moves to another card, the work follows by itself (f49-03) and the plan arrives there for approval.
  - **No terminal commands on the dashboard's pages** (owner, 2026-10-13): the owner signs off and steers from the dashboard, so a page says what to press, not `uv run runner …`.
  - **Reordering is drag, then one send** (owner, 2026-10-13): the owner doesn't like the ↑ ↓ arrows and plans to remove them. They move things freely, press send once, and the runner picks the new order up later (F15).
  - **When a session must close something, it closes it** (owner, 2026-10-13: "make sure that by the end of this session, F107 is archived/planned and it won't happen again"): fix the cause in the session itself when it is the lead's work, and leave the item off the desk, before planning the rest.
  - **Who builds what** (owner, 2026-10-07): a developer first when the ticket is small, unprotected and follows an example in the code, however long it takes; the lead directly when Claude would otherwise end up reviewing, undoing and finishing the developer's work. In an escalation of a poor branch, prefer `reset` and doing it yourself over finishing it.
  - **Mock-ups before UI tickets** (owner, 2026-10-09: "this should be the default for frontend features"): any card that changes what a page shows or how it is laid out gets a mock-up without being asked, with Today and Proposed of the same page on real data, in the same reply as the plan; the UI tickets point at it. Not for wording only, a bug that restores the intended look, or work with nothing on screen ([F72](../milestones/f72-i-really-like-the-mock-up.md)).
