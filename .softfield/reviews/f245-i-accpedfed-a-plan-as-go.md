# Review: F245, an approved card shows as Seed until the runner's next round

**Status:** reviewed, waiting for your sign-off.

### 1. What changed
- When you approve a plan, its card moves from Seed to Planted (or the fast lane) on the board at the runner's next pick, before its first ticket starts, instead of after the whole ticket and review have run.
- Any applied request (a seed, a drop, a merge) now refreshes the board's cards the same way.

### 2. How to test it yourself
1. Plant a small idea on any project and wait for the lead's plan on its thread.
2. Press Approve on the plan.
3. Watch the board from your phone: within the runner's next pick the card leaves Seed and shows as Planted, while its first ticket is still waiting or at work.

### 3. Done when, as of now
- **Met:** D1, an applied request reads the cards again at once: `apply_owner_requests` calls `sync_cards` whenever a request was applied, tested on a real approval and on an idle pick that must not reread the cards.
- **Your check:** the next first-plan approval shows Planted on the board before its ticket finishes.

### 5. Decisions made along the way
- **The cards are reread only when a request was applied, not when only the pause changed.** A pause doesn't move a card, and reading about 250 card files each pick for nothing would slow every round. *The developer on f245-01.*

### 8. How the work went
- A one-line fix with two focused tests, merged on its first attempt in 15 minutes; the review only gave one test fixture a real card's header.

<!-- runner report -->
<!-- /runner report -->
