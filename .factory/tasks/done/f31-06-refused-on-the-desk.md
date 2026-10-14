---
id: f31-06-refused-on-the-desk
milestone: f31-when-i-click-on-approve-plan
difficulty: 6
depends_on: []
agent: lead
priority: 0
files:
  - runner/requests.py
  - runner/metrics.py
  - factory_dashboard/requests.py
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
A request carrying the owner's words that the runner refused is never lost from sight: it waits on the desk, with the words, the reason, Try again and Dismiss, until the owner acts.

### Context
Read `docs/milestones/f31-when-i-click-on-approve-plan.md` D9 and `docs/agents/owner.md` ("Never lose the owner's data"). In `factory_dashboard/planning.py`: `desk`, `coming` and `DeskGroup`; in `factory_dashboard/templates/planning.html`: the desk's groups and the `#plant` form; in `runner/requests.py`: `apply_requests`, `_apply` and how a result is stored; `KINDS` in `factory_dashboard/requests.py`.
- Seven plants were refused on 2026-10-07 ("an idea's title is at most 120 characters") and nothing on any page said so: the owner learned it from the lead hours later. The cause is fixed; this ticket is for every other refusal.
- Words-carrying kinds: `plant`, `plan_message`, `send_back`. Refused means done with a result that isn't that kind's worked result (F6 D1's table).
- A new desk group, "Didn't go through", first on the desk, in the hazard colour, counted in the Planning tab's number and Needs you. Each item: the full text (title and thoughts, or the message), the reason in plain words, **Try again** (fills the Plant form, or the thread's reply box, with the words; nothing is posted until the owner presses Plant it or Send) and **Dismiss** (a new request `dismiss`, subject the refused request's id; the item goes at once, shown as on its way).
- `dismiss` stores the time on the refused row (a new column), and refuses a request that isn't refused or carries no words.
- **Protected work: test-first.**

### Done when
- a plant refused (a card named the same) shows under "Didn't go through" with its title, thoughts and reason, and the Planning count and Needs you count it
- a refused message on F7 shows the same, and Try again opens F7's thread with the message in the reply box, not sent
- Try again on a plant fills the Plant form, not posted
- Dismiss takes the item off at once; after the runner's pick, it stays off; a reload doesn't bring it back
- a worked plant, a refused approval, and a refused pause never show in the group
- with nothing refused, the group isn't drawn
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
