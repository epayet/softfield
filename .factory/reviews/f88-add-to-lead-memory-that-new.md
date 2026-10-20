# Review: F88, new factory work in the factory theme

- **Status:** done, signed off by the owner on 2026-10-20.

## Sign-off sheet

### 1. What changed
Nothing you'll see on a page yet. The lead now has a standing rule: every new factory page, element and mock-up starts out in the dashboard's own industrial look (dark floor, hazard yellow and stripes, Chakra Petch headings, mono labels, corner ticks, plates, machines and crates), a little bolder than needed, so you tone it down instead of asking for more. The game is named only in `docs/agents/owner.md` as where the mood comes from. Nothing is taken from it, and its name never appears on a page or in an asset. Decoration never uses a status colour. Mum's app keeps its calm look.

### 2. How to test it yourself
1. On the dashboard, plant a small factory idea that changes a page (for example "show the queue's total hours on the floor's top bar").
2. When the plan comes back on the card's thread, open the mock-up it links to.
3. Check that Proposed is in the factory theme without you asking for it: hazard yellow, plate headers, angular headings. A calmer variant may sit beside it.
4. Check that the game's name appears nowhere in the mock-up or the plan.

### 3. Left for later
- F81 applies the theme to the pages that already exist. F88 only sets the rule for new work.
- The card's last "Done when" ("the next factory card with a mock-up is themed without being asked") can only be checked on that next card. Step 2 above checks it.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-20 06:42: 1 ticket (lead, difficulty 2), merged on its first attempt, ≈127k Claude token-equivalents, 0 local ([session](../sessions/2026-10-20-0642.md)).
- Lesson: a rule-only card is right for the lead to do in one ticket. A developer would have needed the card's wording anyway.
- The runner stopped after the merge because `runner/prompts.py` changed. That is expected for a prompt change.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** let F81 be the first card that tests the rule, since it has a mock-up on real pages. If its first Proposed comes back plain, turn the prompt sentence into a short checklist (tokens used, plate headers, a calmer variant).

### 7. What clogged the factory line
Little. It was one 39-minute session with one ticket. Most of that time was the lead job itself; there was nothing to wait on and no failed attempt. The only cost was the runner restarting after the prompt change, which is by design. Nothing needs unclogging.

## What was built
- `docs/agents/owner.md`: the "Factory theme" preference (D1–D5), dated 2026-10-09.
- `docs/agents/lead.md`: one line in the Planning room pointing at it.
- `runner/prompts.py`: `PLANNER`'s mock-up paragraph now asks for Proposed in the factory theme from `dashboard.css`'s tokens, leaning bolder, with nothing copied from a game. The game is not named.
- `tests/runner/test_prompts.py`: one new test checks the paragraph's wording and that neither planner prompt names the game. No existing test was edited.

## Findings and resolutions
None. Every "Done when" item that can be checked now is met. The new test anchors on the paragraph itself, not on the whole prompt, so it can't pass on a stray match elsewhere. `tests/runner/test_prompts.py` passes (29 tests). There was no French to check, since nothing in `coucou/` changed. No checkpoint findings to judge. Score: 9/10.

## Backlog
- Added to `docs/backlog.md`: the review job's full test run is longer than one foreground command can run (see below).

## Workflow observations
- The card cites "owner.md, 'Product taste'" for D5, but no such section exists. The new rule's own D5 line now says it directly, so there's nothing to fix.
- In this headless review, the full `tests/runner tests/factory_dashboard` run took 18 minutes, longer than the 10-minute limit for a single foreground command, so it finished in the background: 2405 passed. A review that must keep that suite green can't watch it in one command. Suggested fix, now in `docs/backlog.md`: give the review job a faster check, such as the touched test files plus `softfield check-all`, or a longer limit for headless review jobs.

<!-- runner report -->
<!-- /runner report -->
