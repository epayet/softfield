# Review: F280, The factory's instructions name no project: no Mum, no Coucou paths

- **Status:** done, signed off by the owner on 2026-11-27.

**Status:** round 1 done, ready for your sign-off. Score 8/10. There were two small findings, and the review fixed both itself.

### 1. What changed
- Lead jobs in every project now write "What changed" and "What next" for the people named in that project's `.softfield/project.md`, or for you when it names nobody. They no longer write for "Mum".
- The factory's instructions, prompts and gate hints no longer name Coucou's folders, its French or its JavaScript rules. A test fails if "coucou" or "Mum" comes back. Coucou's removed text is kept word for word on the card.

### 2. How to test it yourself
1. Open a project that isn't Coucou (travel-companion, say) and check that its `.softfield/project.md` says who the project is for. Add a line if it doesn't.
2. Let that project's next milestone reach its review, then open its sign-off page on your phone.
3. Check that "What changed" and the quoted "What next" ideas talk about the people its `project.md` names (or about you), and never about Mum.

### 3. Done when, as of now
- **Your check:** a new project's sign-off sheet and its "What next" don't mention Mum. The instructions no longer ask for it, but the first new sign-off will show it (steps above).
- **Met:** `test_the_factorys_own_instructions_name_no_project_and_no_mum` fails on the old `runner/instructions/lead.md` ("the owner and Mum") and passes now. The whole suite is green: 4091 passed.
- **Met:** Coucou's removed instructions are in "For Coucou" on the card, word for word. The review added the two lines the ticket had missed: the owner file's "calm, ambient look" line and the F94 lesson's Preact sentence.

### 5. Decisions made along the way
- **The gate list in `docs/workflow.md` now says the translations check runs only where a project turns it on, and no longer says "French".** The ticket left "French" there, against D1. *The review.*
### 6. What next
- **Factory:**
  > Make the leak test in `tests/runner/test_prompts.py` also catch a project's language ("French") in the factory's instructions, so the next leak like F280's `docs/workflow.md` line is caught by the test and not by the review.
  > When a project's `.softfield/project.md` doesn't say who the project is for, show that on its Projects page with a box to fill it in, so its sign-off sheets stop falling back to me.

### 7. Left for later
- Coucou's own card moves the "For Coucou" text into Coucou's `.softfield/project.md` and `.softfield/developer.md` (D4). A Softfield job can't write to Coucou's repo.

### 8. How the work went
- The ticket fixed every leak the card listed. The two it missed are words the test doesn't look for ("French", and a line the card had no slot for), so a test that only searches for names misses a leak of the same kind written in other words.

<!-- runner report -->
<!-- runner report -->
