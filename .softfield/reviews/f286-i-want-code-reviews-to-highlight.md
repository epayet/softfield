# Review: F286, Reviews look for complexity and leave the code simpler (Boy Scout rule)

- **Status:** done, signed off by the owner on 2026-11-25.

**Status:** round 1 done, ready for your sign-off.

### 1. What changed
- Every review now looks for complexity after bugs: what the milestone itself added (a repeated helper, dead code, a second way of doing one thing) is a should-fix; older tangles in the files it touched come to you as at most two quoted lines starting "Simpler:" to plant.
- The numbers below gain a "Code lines" row (added and removed, leaving out tests, docs, `.softfield/` and Markdown) and a "Net code lines" column for every milestone, so you can see whether the code grew or shrank. A review says it in words when a milestone shrank it.
- Softfield's own reviews treat Softfield as the product: no "Product: on hold" line, and up to two feature ideas that follow from the milestone, under Factory. No brief mentions French any more.
- A plan that adds a module, table, setting, job kind or page now names what it builds on and what it makes removable, with the removal as a ticket in the same plan.

### 2. How to test it yourself
1. On this milestone's page, under Results, find the "Code lines" row and, in Trends, the "Net code lines" column with a value on every milestone.
2. Read this sheet: no Product bullet, and "What next" holds feature ideas under Factory.
3. On the next review page after this one, look for a "Simpler:" line under What next, or none when the files were clean.
4. Plant a card that adds something new; its plan's Decisions should say what it builds on and what it makes removable.

### 3. Done when, as of now
- **Your check:** the "Code lines" row and the "Net code lines" trend: the runner writes them into this review's numbers; this milestone's merged tickets come to +92 −13 lines of code.
- **Met:** a duplicate the milestone added is graded should-fix and routed: this review found `commit_code_lines` repeating `commit_size`'s parsing and merged them.
- **Your check:** older complexity as at most two "Simpler:" lines: the brief asks for it; this review found none in the touched files worth a run, so the first one comes with a later review.
- **Met:** the planner's brief asks a new mechanism to name what it builds on and what it makes removable; **Your check:** the next plan that adds one shows it.
- **Met:** this review's brief and sheet have no Product bullet; its ideas are under Factory.
- **Met:** neither the review brief nor the workflow's review loop mentions French.

### 5. Decisions made along the way
- **The factory's brief is the general one with two phrases swapped** (`REVIEW_FACTORY`), chosen by the existing "is this Softfield" check in `runner/stacks.py`. One brief to maintain instead of two; the other option was a `{field}` filled per project. *Lead, f286-01.*
- **"Say it when the code shrank" added to the briefs.** ADR 52 item 4 asks for it, but neither ticket carried it. *The review.*

### 6. What next
- **Factory:**
  > Show each milestone's net code lines on its card in the board and on the milestone page beside its cost, so I can see which milestones grew the code without opening the review.
  > When a review's "Simpler:" lines keep naming the same file, plant a card to split or trim that file instead of collecting more lines about it.

### 8. How the work went
- The ADR's items were split across two tickets and one sentence of item 4 fell between them; a plan that cites an ADR item by item should map every item to a ticket.
