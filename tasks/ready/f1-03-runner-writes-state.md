---
id: f1-03-runner-writes-state
milestone: f1
depends_on: [f1-02-runner-writes-jobs]
agent: lead
difficulty: 6
files:
  - runner/loop.py
  - runner/milestone.py
  - runner/owner.py
  - runner/metrics.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_milestone.py
  - tests/runner/test_owner.py
---

### Goal
The runner keeps the database's projects, milestones, tickets, findings and owner items current, so the dashboard never reads the repo.

### Context
Read `docs/milestones/f1.md` (D2, D4, D8) and `runner/metrics.py`. Test-first.
- **Project:** the repo folder's name, its path, and `[project] description` from `workflow/runner.toml` (add it; one line about Coucou).
- **Tickets and the queue (D4):** at session start, upsert every ticket in `tasks/*/` with its state (folder), title (goal), body, kind, `depends_on`, files and `difficulty` when present; then on every move (`running`, `done`, `escalated`, `blocked`). A merge records `merged_by`, the commit and lines changed (git numstat of the squash commit).
- **Milestones:** `runner milestone` upserts its milestone with the title, `Outcome` and `Done when` sections of `docs/milestones/<key>.md`, dates, verdict and review rounds.
- **Findings:** each review round's JSON (`runner/review.py`'s `parse_review`) becomes `findings` rows on that review job, keyed by the finding id.
- **Sign-off sheet:** after the review, the sections of `docs/reviews/<key>.md` (What changed, How to test it yourself, What next, Left for later, How the work went) go into `milestones.signoff`, a heading missing leaving its key out.
- **Owner items (D8):** the verdict's items (an ADR a job drafted and its question, a blocked ticket, a review stop), sign-off waiting (with the device steps), each as a row; resolved when done: `runner signoff`, `runner accept`/`reject`, a rerun that clears the blocked ticket. The stale-heartbeat item is the dashboard's, not the runner's.

### Done when
- after a session, every ticket in `tasks/` has a row whose state matches its folder, and a merged one has `merged_by`, commit and lines changed
- a milestone row carries its outcome and Done when; after a review, its sign-off sections and findings
- a blocked ticket and a drafted ADR each leave an open owner item with a command; `signoff` and `accept` resolve theirs
- the same session twice leaves the same rows
- `uv run runner check-all --task f1-03-runner-writes-state` passes
