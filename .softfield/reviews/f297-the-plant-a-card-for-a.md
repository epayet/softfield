# Review: F297, the Projects page's plant buttons also ask the lead

- **Status:** done, signed off by the owner on 2026-11-27.

**Status:** round 1 passed; the review fixed three test checks itself. Ready for your sign-off.

### 1. What changed
- On `/projects`, a project without a stack now offers "Plant and ask the lead for a stack": one press plants the card and sends it to the lead, so the plan arrives on the card's thread without a trip to Planning.
- A crashed app or a failed update offers "Plant and ask the lead to fix it", on its plate and in Needs you, and asks the lead the same way. After a press, the line says "On its way: the runner plants it and asks the lead at its next pick".

### 2. How to test it yourself
1. On your phone, open Projects: coaster-ranker and coucou show "Plant and ask the lead for a stack".
2. Press it on one of them: the button goes and the on-its-way line shows.
3. After the runner's next pick, open Planning for that project: the new card is there with the lead's reply on its thread, and you didn't press anything else.

### 3. Done when, as of now
- **Met:** both buttons send a `plant` request with `"ask": true` (tests check the stack and both fix values).
- **Met:** the labels and the on-its-way line say the lead is asked, in all three places.
- **Your check:** press one on a project without a stack and find the lead's reply on the new card's thread. The runner already queues the lead for an asking plant (your own F297 and F300 plants show "queued for the lead"), but no stack button has been pressed since the change.

### 6. What next
- **Factory:**
  > Simpler: the plant button and its on-its-way line are written out three times (twice in factory_dashboard/templates/projects.html and once in _partials/app_row.html); one small Jinja macro taking the project, the value and the label would save about 8 lines and keep the wording from drifting apart.
  > When a ticket renames a label, the developer should search the tests for the old words too, because a "not in the page" check on the old label passes forever once nothing shows it.

### 8. How the work went
- The developer did a one-attempt rename with the right value change. It missed three negative test checks on the old label, which had stopped testing anything. The review fixed them in 3 lines rather than spend a run.

<!-- runner report -->
<!-- runner report -->
