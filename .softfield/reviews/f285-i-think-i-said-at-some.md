# Review: F285, Copilot pre-reviews a finished milestone while Claude is out

**Status:** round 1 done, ready for your sign-off.

### 1. What changed
- When Claude is at its real limit and nothing else can start, Copilot now reads a finished milestone whose review waits for Claude (its card, done tickets and the files they changed) and files developer fix tickets for what it finds, instead of the line standing idle.
- At most three per milestone, and only after a new merge since the last one; within Copilot's monthly pace. The Opus review later judges its findings. The milestone's page lists the cost under "Copilot's pre-reviews", and the top bar says "Copilot reads F… before the lead's review".

### 2. How to test it yourself
1. Wait for a day when Claude shows 100% (or a rest) on the Overview, with a milestone's review waiting and no developer ticket in ready.
2. On a computer, `softfield run --dry-run` should end with "next: Copilot's pre-review of F…".
3. Leave the runner going: the top bar shows "Copilot reads F… before the lead's review", and any fix tickets it files appear in Tickets, for a developer.
4. On that milestone's page, under Results, "Copilot's pre-reviews" shows its cost; after its review, the Findings list holds its findings with the lead's verdicts.
5. A fourth pre-review of that milestone never comes, and none comes again until a fix ticket merges.

### 3. Done when, as of now
- **Met:** f285-01, f285-02 and f285-03 are merged.
- **Met:** ADR 51 is Accepted (by you, 2026-11-24).
- **Your check:** no pre-review has run on the live line yet (no `pre-review` job in the database); the first Claude-out day is the real test.

### 5. Decisions made along the way
- **The pre-review reads only its tickets' own merges.** The built job listed every file changed since the milestone began, so F285's own pre-review would have been handed F97's dashboard files, merged in between. D1 named the `<milestone>-start` tag first, which has the same flaw. *The review.*
- **A finding that filed no ticket is always recorded as `report`.** The job kept whatever route Copilot wrote, so a protected-file finding could show as "local" with no ticket behind it (D4). *The review.*

### 6. What next
- **Factory:** after Copilot's first two or three pre-reviews, compare their findings with the Opus review's verdicts in that factory review, to see whether three rounds per milestone is too many or too few.

### 8. How the work went
- Two Sonnet lead tickets and one local-model ticket, all passed on attempt 1; the local model took 37 minutes for two labels and their tests.
- "Files since the milestone's start" is wrong whenever the board interleaves cards, which is now usual. Any job that reads one milestone should take its tickets' own merges. Recorded in ADR 02's learnings log.

<!-- runner report -->
<!-- /runner report -->
