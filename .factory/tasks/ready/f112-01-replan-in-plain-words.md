---
id: f112-01-replan-in-plain-words
milestone: f112-plain-words-for-replan
difficulty: 3
depends_on: []
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The dashboard says "Change to queued tickets" for a replan proposal and "plan check" for the lead's replan ticket, so the bare word "replan" is on no page.

### Context
Read `.factory/cards/f112-plain-words-for-replan.md` (D1, D2). In `factory_dashboard/planning.py`: `_KIND_COLOR`, the `Proposal` dataclass and where a `Proposal` is made; `_open_proposals`, whose item's words fall back to the proposal's kind; `_plan_changes`, which lists what approving a replan changes, each with its `word` ("added", "changed", "set aside" or "removed"). In `factory_dashboard/templates/thread.html`: the line `{{ prop.kind | upper }} · …` of a proposal's box. In `factory_dashboard/templates/proposal.html`: the line "Approving this replan applies the ticket changes at once…". In `factory_dashboard/templates/_partials/queue.html`: the `{% for t in next %}` row of a ticket. The tests to follow: `test_a_replan_shows_what_approving_changes_with_each_text` in `tests/factory_dashboard/test_planning.py` and `test_next_in_line_names_a_due_review_first` in `tests/factory_dashboard/test_overview.py`.
- **A kind's words:** beside `_KIND_COLOR`, a dict of the words each kind shows: `adr` "ADR", `mockup` "Mock-up", `plan` "Plan", `seed` "Seed", `merge` "Merge", `replan` "Change to queued tickets". `Proposal` gets a field holding them, and the templates show that field where they showed the kind.
- **The desk:** where an open proposal's item fell back to its kind for its words, it uses the same words.
- **The review page of a replan:** the sentence becomes "Approving this applies the ticket changes at once, even while paused, and resumes the line." Above "What approving changes", one line counts them from `_plan_changes`, in this order and leaving out a zero: "2 changed, 1 added, 1 set aside".
- **Next in line:** a ticket whose id ends with `-replan` is followed, after its id, by a small "plan check" in the row's muted style.
- Change nothing in `runner/`, in a request's values, or in any `kind ==` test of the templates: only what is shown.

### Done when
- a thread with a replan proposal shows "CHANGE TO QUEUED TICKETS" in its box and no "REPLAN"; a plan still shows "PLAN"
- a replan's review page reads "Approving this applies the ticket changes" and counts its changes: "1 changed, 1 added, 1 set aside" for the fixture of the test to follow (`_replanned`: one ticket changed, one set aside, one added)
- none of that page's own labels or sentences says "replan" (the ticket texts it shows, such as "the replan's a", and its address still do): assert on the tab's label, the "What happens next" steps and the count line
- an open replan with no key points shows "Change to queued tickets" as its words on the desk
- in Next in line a ready ticket `f1-07-replan` is followed by "plan check"; `f1-05-first` is not
- the buttons still post the same requests (the existing tests of Approve and Send back pass unchanged)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
