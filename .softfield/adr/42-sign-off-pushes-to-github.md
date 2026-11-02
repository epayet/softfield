# ADR 42: The owner's sign-off pushes the milestone to GitHub

- **Status:** Accepted (by the owner, 2026-11-02)
- **Date:** 2026-11-02
- **Deciders:** project owner (accepts), Claude (drafts)
- **Evidence:** The owner, 2026-11-02: push to GitHub at the end of milestones, deterministically. `epayet/softfield` exists, public and empty; no project has a remote. A scan of all history found no keys or tokens; planning threads do hold pasted logs, so a later paste could carry one.

## Decisions
1. **Sign-off is the only trigger.** No model decides and no agent ever runs `git push`; the runner does it.
2. ⚑ **A project opts in by having an `origin`** (amended by the owner, 2026-11-02, replacing a `remote` line in `project.toml`): if the origin is set, it pushes; otherwise it doesn't. Softfield has one; Coucou and Travel Companion stay local until someone sets theirs, so scan a repo before you do.
3. **What goes:** main up to exactly the sign-off commit and its `<key>-done` tag. Never a task, plan or superseded branch. Tickets merged after that sign-off wait for the next one.
4. **When:** at each runner pick, any `-done` tag missing from the remote is pushed. A failed push retries by itself; a repeated sign-off changes nothing.
5. **Never `--force`.** A diverged remote stops the push; work carries on.
6. **A secret check runs first,** in plain Python with no new dependency, over the commits about to go: key patterns, risky file names, this machine's ntfy topic. A hit holds the push and names the file and line, never the value.
7. **On screen:** a desk item only when a push keeps failing, the remote diverged or the secret check holds it. No new panel.

## Alternatives turned down
- **Push when the review passes:** fresher, but publishes work the owner hasn't checked on their devices.
- **Push on every merge:** public main would carry half-finished cards.

## Consequences
- The public main is always a state the owner accepted, and it lags by however long sign-off takes.
- Sign-off is not a backup: work between sign-offs has no off-site copy. A daily git bundle beside the database backup is a separate card.
- A pattern check can't catch everything, and what's public can't be recalled. It is a backstop.

## What doesn't change
The sign-off itself, its tag and its commit. Other work never waits for a push.
