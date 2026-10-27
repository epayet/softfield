---
id: f80-01-by-kind-of-work
milestone: f80-developer-rating-could-be-more-tailored
difficulty: 4
depends_on: []
files:
  - factory_dashboard/agents.py
  - factory_dashboard/templates/agents.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_agents.py
tests:
  - tests/factory_dashboard/test_agents.py
---

### Goal
The Agents page gets a "By kind of work" bay: for each agent and kind of ticket (Pages, Code, no pages), its coding score beside what its rating expected.

### Context
Read `.factory/cards/f80-developer-rating-could-be-more-tailored.md` (D1–D3), then the picture to build: `.factory/cards/f80-mockup/by-kind.html` (Proposed).
- Follow `rating_data` in `factory_dashboard/agents.py` for the query and the project and milestone filter, and its tests in `tests/factory_dashboard/test_agents.py` for seeding `rating_changes` and `tickets`.
- Add `work_kind(files)` (D1) and a function returning one row per agent and kind with tickets, score, expected and the gap's words (D2, D3), and pass it to `agents.html` from `agents_page`.
- Expected per game is `expected` in `runner/ratings.py`, with the row's `before` and the ticket's `difficulty_corrected`, else `difficulty`; skip a game whose ticket has neither.
- The bay sits after Efficiency. New styles use the tokens at the top of `factory_dashboard/static/dashboard.css` only; each agent's colour is its existing token (`--opus`, `--qwen`…), as the floor uses them.
- The dashboard is English only: no translation needed.

### Done when
- a ticket with `factory_dashboard/templates/x.html` in its files counts as Pages, one with only `.py` and `.md` files as Code, no pages
- with an agent's games merged first (1), merged later (0.5) and not merged (0) on page tickets, its Pages row shows their count and average score, and expected is the average of `expected(before, difficulty)` over the same games
- bench games (`result` starting `bench `) and finding penalties (`finding `) are not counted
- a gap above +5 reads "better", below −5 "worse", else "as rated"; a row of fewer than 3 tickets says "too few to say"
- the milestone filter limits the bay as it limits Ratings over time; with no coding games the bay says so in one line
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: BLOCKED: needs-file
attempts: 2
tokens: 11196656
logs: .factory/var/runs/20261027-005355/f80-01-by-kind-of-work
```
