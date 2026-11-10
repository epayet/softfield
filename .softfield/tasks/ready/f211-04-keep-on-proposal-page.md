---
id: f211-04-keep-on-proposal-page
milestone: f211-a-plan-must-not-get-lost
difficulty: 2
depends_on: [f211-03-open-plan-on-thread-page]
files:
  - factory_dashboard/proposal.py
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_proposal.py
---

### Goal
On a signed-off card a plan's page offers "Keep it as a new card" in place of Approve plan.

### Context
The picture to build is `.softfield/cards/f211-mockup/open-plan.html`, picture 5. Read `.softfield/cards/f211-a-plan-must-not-get-lost.md`: D6 and D8.
- `factory_dashboard/proposal.py`: `proposal_review` builds the page's values; `factory_dashboard/templates/proposal.html`: `#primary` holds Approve plan, and a press marks `#actions` on its way. The page's `clash` (`plan_clash`, F139) asks for "Refresh against main" when the branch clashes; the old branches of signed-off cards (plan/f51, plan/f82) all clash.
- F224's `details#approve-first` (`f224-02-approve-first-on-the-pages`) sits beside `#primary` once it lands.

### Done when
- a done card's open `plan`, `replan`, `mockup` or `adr`: Keep stands in `#primary` in place of Approve plan or Accept ADR, with one line saying a signed-off card takes no plan; Send back and Reject stay
- on a done card there is no `#approve-first`, and no clash line or Refresh against main: Keep re-drafts on today's main anyway
- a card that isn't done: the page as it is today
- a kept proposal's page reads "Kept as a new card" and has no button
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
