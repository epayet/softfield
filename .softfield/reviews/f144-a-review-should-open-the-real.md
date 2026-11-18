# Review: F144, a review reads the real page and real data before the tests

## Sign-off sheet

### 1. What changed
Milestone reviews now open the real page before they read the tests. When a milestone changes a dashboard page, the review brief asks the lead to:
- read that page on the live database (`softfield look page`), plus its raw HTML where escaping or an attribute matters;
- compare one fixture from each new test file with a real card, thread or row;
- name, in the review report, the pages it opened and the record it compared.

A fixture tidier than the real thing becomes a should-fix finding. The lead's "Review" notes say the same thing and point to ADR 37. You won't see anything new on the dashboard. What you should notice is fewer review sign-offs with a bug that only real data shows: F109, F94, F30 and F158 all had one. This review got the new brief itself (see "Findings").

### 2. How to test it yourself
1. Wait for the next milestone that changes a dashboard page, and open its review on the dashboard.
2. In the review's "Findings" section, look for one line naming the page or pages it opened and one naming the real record it compared.
3. If the milestone added a new test file and the review doesn't mention a fixture, the check was skipped. Tell me on the card's thread.

### 3. Left for later
Nothing.

### 4. Decisions waiting for you
None. ADR 37 was accepted on 2026-10-28.

### 5. How the work went
- 2026-11-18 18:01 ([session](../sessions/2026-11-18-1801.md)): 1 ticket, merged on the first try by the lead in 9.6 minutes. It was a lead ticket because it is prompt text in the protected `runner/`, so the local model did no work.
- Lessons:
  - A brief-only change sized as one lead ticket is the cheapest route: no checkpoint and no fix round.
  - The new test checks the order of the instructions (the page look comes before "Read the tests"), not just that the words are there. That is the right way to test prompt text.

### 6. What next
- **Product:** product work is on hold, so nothing here.
- **Factory:** the reviewer still has to work out which page addresses a diff touched. The runner already knows the changed files, so it could name the pages in the brief and make the look harder to skip.
  > The review brief should list the dashboard pages a milestone's diff changed (worked out from its factory_dashboard/ templates and views), so the reviewer opens each one without having to guess the address.
- **Factory:** the review brief tells the reviewer to keep a plain `uv run pytest -q tests/runner tests/factory_dashboard` green. Run one test at a time, that suite took more than 20 minutes in this review and never finished, while `softfield check-all` passed in a few minutes on parallel workers.
  > The review brief in runner/prompts.py should name `softfield check-all` (or pytest on parallel workers) as the check to keep green, not plain `uv run pytest tests/runner tests/factory_dashboard`, which now runs past the review's 10-minute command limit.
- **Factory:** after two or three page milestones, check the reviews' "Findings" sections for the opened-page line. If one is missing, the runner could check for the line before it accepts the review.

### 7. What clogged the factory line
The work itself took 9.6 minutes (run 20261118-180129). The card waited from its plan on 2026-10-27 until today: first for ADR 37 to be accepted (2026-10-28), then for its turn in the board order. That wait is the queue doing its job, not a clog. Nothing to unclog.

## What was built
- `runner/prompts.py` `REVIEW`: a paragraph before "Read the tests…" covers ADR 37 items 1–2 and the case where the live database lacks the new state. The report instructions gain item 3 (name the pages opened and the record compared). All the format fields are unchanged and still match `runner/milestone.py:784`.
- `runner/instructions/lead.md` "Review": the screenshot bullet now says to read a changed factory page with `softfield look page` (ADR 37), and keeps screenshots for product pages.
- `tests/runner/test_prompts.py`: two new tests. One checks that the page look comes before the tests paragraph, carries all its parts and still formats with the runner's fields. The other checks that the lead's notes name `look page` and ADR 37. No existing test was edited.
- ADR 37 item 4 (reviews only) holds: the checkpoint and developer prompts are untouched.

## Findings and resolutions
None. The diff does what ADR 37 asks, and its tests check order and content.

- **Pages opened:** none. The diff changed no page under `factory_dashboard/`; it only touched `runner/` and its tests.
- **Record compared:** none. There is no new test file, only two tests added to the existing `tests/runner/test_prompts.py`, and their only fixture is the format fields, which I checked against the real call at `runner/milestone.py:784`.
- **French:** no change under `coucou/locale/`.
- **Tests:** `tests/runner/test_prompts.py`: 42 passed, and `softfield check-all` passed (ruff, mypy, translations, layout and every test). A plain serial `pytest` of `tests/runner tests/factory_dashboard` took more than 20 minutes and was stopped at the time limit; `check-all` spreads the same tests over parallel workers.

## Set aside
Nothing.

## Factory
- **Flow:** one lead ticket, merged on the first try. No stops, no checkpoint (lead ticket), no parks, and nothing needed from you.
- **Models:** Claude only, about 101k token-equivalents for the ticket (session report). The local model did no work, as planned for protected prompt text.
- **To change:** see the two Factory items under "What next".

## Numbers
<!-- runner report -->
<!-- /runner report -->
