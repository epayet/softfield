# Discoveries inbox

Any agent may append **one bullet** here when it notices unplanned work: a bug, a missing test, a refactor idea. **Never fix it in code.** Claude triages this inbox at each milestone review.

Format: `- [task-id] file:line: what you noticed`

- [m4-lead] tests/browser/test_live.py: `test_after_a_401_it_signs_in_and_reopens_from_the_last_event` failed once in a full run (2026-09-29) and passed 3/3 alone: a timing flake. Watch it in the developers' `all-tests` gate.
