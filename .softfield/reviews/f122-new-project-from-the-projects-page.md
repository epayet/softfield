# Review: F122, start a new project from the Projects page

- **Status:** done, signed off by the owner on 2026-11-19.

## Sign-off sheet

### 1. What changed
- **A "Start a project" panel** at the bottom of the Projects page: the idea, a name, "built with" and "an app I open in a browser". Start draws the new plate at once, dashed orange, "On its way".
- **The runner makes the project itself:** its folder under `~/projects/epayet/`, your idea word for word in its seed, a first card M1, registered "setting up"; then the lead sets it up headless and replies on M1's thread with ADR 00 to approve.
- **Approving ADR 00 adds it to the factory** when `create`'s checks pass (unpaused, M1 planned); if they fail, the lead is sent back twice at most, then it stops on your desk.
- **A project being set up** shows its line of four stations (Asked, Set up by the lead, ADR 00 for you, In the factory) and "Answer on its first card →". If the runner can't make a project, your idea now waits on the desk under "Didn't go through" until you dismiss it.

Matches the mock-up for the panel. The two new plates (on its way, setting up) aren't in the pictures: the live data has no such project yet, so they rest on the tests. "Goes in" now reads `~/projects/epayet/` as in the mock-up (the pictures show the full path, fixed by this review).

### 2. How to test it yourself
1. On your phone, open Projects, scroll to "Start a project", write a two-line idea for a tiny app, name it, leave "an app" ticked, press Start it: the dashed plate appears at the end of the list at once.
2. After the runner's next pick, the plate becomes a real one with "Set up by the lead" lit; within the hour (or after a limit), "ADR 00 for you" lights and the desk counts it.
3. Press "Answer on its first card →": the lead's points and ADR 00 with its Approve are on M1's thread. Approve it.
4. Back on Projects: the plate has its place, Board and Overview, and an app row; press Run and open its one page.
5. Send one more with only spaces as the idea: it shows under "Didn't go through" on the desk with Dismiss.

### 3. Done when, as of now
- **Your check:** you start a small app from your phone, approve its ADR 00 on M1's thread, press Run on its plate and see its one page. The whole path is tested piece by piece, but no project has gone through it for real yet: the setup job has never run against a real Claude.

### 5. Decisions made along the way
- **M1 carries no priority.** ADR 45 retired the field after D2 was written. *The lead, f122-04.*
- **A setting-up plate keeps its Planning link** beside "Answer on its first card →"; the mock-up showed only the latter. Harmless, and the desk is one tap away. *Developer and lead, f122-05.*
- **A refused new project goes to the desk with Dismiss but no Try again,** since sending the same words again would make a second folder; the words are on the item to copy. *The review.*
- **"Goes in" shows the folder as `~/…`, with the name as typed,** not the runner's slug (which may take `-2`). *The review, after f122-05.*

### 6. What next
- **Product:** product work is on hold; the first real use of this card is the suggestion.
- **Factory:**
  - A Start whose send fails still looks sent.
    > On the Projects page, if the Start a project send fails (htmx:responseError or sendError in `factory_dashboard/templates/projects.html`), remove the dashed plate it drew and re-enable the form, so a failed send never looks on its way.
  - A rare failure half-way through making a project leaves it stuck.
    > In `runner/setup.py` `start_project` and `runner/requests.py` `_new_project`, if registering the project, publishing its cards or queuing its setup fails after the commit, undo the row and the folder too, so a failed start never leaves a project stuck on "Asked" or makes the next one `-2`.

### 7. Left for later
- On a wide screen "(optional)" wraps under BUILT WITH, so its box sits a little lower than Name's. Cosmetic.

### 8. How the work went
- The four lead tickets (runner side) passed first time on Claude for $12; the page ticket was the local model's and failed three times (two 20-minute stops with no edit, one timeout) before the lead finished it from its branch for $2.16. A page with a JS form, a `<template>` and four station states was too wide a ticket for the local model; splitting the panel from the plates would have suited it better.
- The replan (f122-04, $0.41 on Sonnet) paid off: f122-05's context named the real fields, and the page needed no rework against the runner.
- The review found a gap no ticket owned: the waiting plate vanishes when a request is done, so a refusal needed the desk. A new request kind carrying the owner's words should list itself in `owners_words` from the start.

### 9. What clogged the factory line
- **f122-05, 2 h of local attempts** (04:36–06:36) before the escalation: two "no edit after 20 min" stops and a 75-minute timeout. Unclog: split UI tickets with a script from their markup ones.
- **f122-03, a 2 h 20 wait** (01:48–04:08) parked on Claude's usage limit; nothing to change.

<!-- runner report -->
<!-- /runner report -->
