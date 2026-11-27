# Review: F132, One view of the whole factory: the top bar, the Overview, Jobs and the floor

**Status:** round 1 done, ready for your sign-off. Score 8/10. Two should-fix findings in While you were away (a broken link to another project's blocked ticket, a long copy loop) and one tidy test fixture, all fixed by the review.

### 1. What changed
- The Overview is the same page whichever project you pick. Now, Next in line (in the runner's order across projects, with a "Passed over" line when a project ahead has nothing to run), Needs you (one desk line per project) and While you were away cover every project, and each item has its project's plate.
- The floor, on the Overview and on `/line`, is one floor. The field, the machines' crates, Merged today and the stash count every project, and a crate's label starts with its project.
- Jobs, Runs and the Timeline list every project's jobs with a Project column (none when you have only one project). The Timeline opens on the last 24 hours instead of one card.
- The project picker now sits in the tab strip with Planning, Board and Tickets, and the factory-wide pages' breadcrumb reads "The whole factory · 5 projects". Savings from delegating moved to each project's page, counted over all its milestones, and the Claude per milestone chart is gone.

### 2. How to test it yourself
1. While a softfield job runs, open the Overview on your phone and pick travel-companion, then coucou, in the picker beside Planning. The bar and Now show the same softfield job both times.
2. In Next in line, check that the count reads "N tickets waiting: softfield … · travel-companion …" and that each row ends with its project's plate.
3. In Needs you, tap "Open ›" on travel-companion's desk line: travel-companion's Planning opens.
4. In While you were away, tap a merged or blocked ticket of a project you haven't picked: its own ticket page opens.
5. Open Jobs, then Timeline: rows from several projects together, each with its project. Then open Projects › softfield: "Savings from delegating on softfield, so far" is at the bottom.

### 3. Done when, as of now
- **Met:** f132-01 to f132-08 are merged, along with the two checkpoint fixes (09, 10).
- **Met:** while softfield's review ran, travel-companion's Overview on the live dashboard said "Running: softfield · review F132", and Now showed that job. Needs you had travel-companion's and softfield's desk lines, and the queue counted all five projects. The tests check that each project's Overview is the same page and that "Passed over" says why. **Your check:** the same thing on your phone, and the developer's blue dot when a developer ticket runs.
- **Met:** Jobs on the live dashboard lists softfield, travel-companion, coucou and wardrobe-teller jobs together, each with its project. The Timeline does the same for the last 24 hours.

### 5. Decisions made along the way
- **Factory-wide pages say so with a flag on `render`, not by reading the page's tab.** The project page and the Projects list share the Projects tab, so the tab alone can't tell a project's page from a factory-wide one. *Developer, f132-08.*
- **The Timeline's milestone filter keeps to the picked project.** Card keys like "m8" repeat across projects. The default view, the last 24 hours, stays every project's. *Checkpoint, then developer, f132-09.*
- **With one project, Jobs, Runs and the Timeline have no Project column at all**, rather than a column that repeats the one name. *Checkpoint, f132-09 and f132-10.*
- **A blocked ticket in While you were away has its plate and its own project's link.** D2 asks this of every factory-wide row, but the ticket's diff left this older line alone. *The review.*

### 6. What next
- **Factory:**
  > On the Overview, let me tap a project's plate to show only that project in Now, Next in line and While you were away, with one tap back to the whole factory.
  > On the floor, give each project's crates a small mark of its own (a letter in ink, not a colour) so on a phone I can tell whose crate is whose without reading the label.
  > Simpler: in `factory_dashboard/queries.py`, `away()` walks its jobs four times (last job, attempts, first start, and each merged ticket's developer outcomes rescanned per row); one pass building a record per ticket would save about 20 lines and the per-row rescan.

### 8. How the work went
- A factory-wide view needs every link checked, including markup the ticket doesn't touch. 03 made the blocked list cover every project, but its link was older markup, so neither the developer nor the checkpoint read it. The review found it on the live page, with a 404.
- 03's first two attempts stopped ("no edit after 20 min") while the developer was still reading the card and its mock-up. A ticket that points at a large card should quote the lines it needs.
- The lead's two tickets (02, 05) set the plate and `every_project` first, and the six developer tickets copied them. Four of those passed first time, which shows the order paid off.

### 9. What clogged the factory line
- 01 lost about 2 h 25 min to two local attempts: one timed out at 75 min, the other failed on the full suite's 1200 s gate timeout, not on its code. It escalated.
- 08 took about 2 h 30 min over three attempts: a timeout, then a failure on three existing phone tests that still put the picker on the brand's row. A ticket that moves an element should name the existing tests that pin where it sits.

<!-- runner report -->
<!-- runner report -->
