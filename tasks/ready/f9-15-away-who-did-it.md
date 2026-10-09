---
id: f9-15-away-who-did-it
milestone: f9-line-polish
depends_on: [f9-31-fix-away-swap-nests-section]
difficulty: 4
files:
  - factory_dashboard/templates/_partials/away.html
  - factory_dashboard/queries.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Each ticket under "While you were away" shows who did it as a clear label at the start of its row (Qwen, gpt-oss-120b, Claude Opus…), how many attempts it took, and whether Claude did it as a lead ticket or finished a developer's; the summary line names the blocked tickets.

### Context
Read `away` and `AwayTicket` in `factory_dashboard/queries.py`, `factory_dashboard/templates/_partials/away.html` (today a small "(merged by …)" after the title) and `_name` in `factory_dashboard/line.py`, which names agents on the floor: use the same names. The style to follow is `.agent` in `factory_dashboard/static/dashboard.css` (the Running panel's agent names).
- The owner (2026-10-06): "i'd like to see who did each ticket as well a bit clearer".
- `merged_by` holds an agent id (`local-qwen3.6-35b-a3b`, `claude-opus`, `ollama-gpt-oss-120b`), or nothing for old tickets: then no label.
- Attempts: the ticket's developer jobs in the metrics database; say "1st try" or "3 attempts".
- The owner (2026-10-07): "while you were away says 1 blocked, but i don't know which one… when it says a ticket was merged by claude, was it a lead ticket or a developer ticket escalated? it could be clearer".
- Lead or finished: the ticket's `kind` (`lead` or `developer`) in the `tickets` table. A developer ticket merged by `claude-opus` reads "Opus · finished after 3 developer attempts"; a lead ticket, "Opus · lead ticket".
- "N blocked now" becomes "blocked now: " and each blocked ticket's id as a link to `/tickets/<id>` (the same rows `away` counts in `blocked`).

### Done when
- a merged ticket by `local-qwen3.6-35b-a3b` after two developer jobs shows a "qwen3.6-35b-a3b" label and "2 attempts"; one by `claude-opus` in one job, "Opus" and "1st try"
- a ticket with no `merged_by` shows no label
- a developer ticket merged by `claude-opus` after 3 developer jobs reads "finished after 3 developer attempts"; a lead ticket, "lead ticket"
- with one blocked ticket, the summary line links it by id
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
