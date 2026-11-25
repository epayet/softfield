---
id: f296-02-code-lines-on-the-milestone-page
milestone: f296-show-each-milestone-s-net-code
difficulty: 2
depends_on:
  - f296-01-code-lines-kept-per-ticket
agent: developer
files:
  - factory_dashboard/queries.py
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_queries.py
  - tests/factory_dashboard/test_milestones.py
tests:
  - tests/factory_dashboard/test_queries.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A milestone's page says how much code its merged tickets added, beside what it cost: on the closed "What it cost" fold and inside it.

### Context
Read `.softfield/cards/f296-show-each-milestone-s-net-code.md` (D3, D4). The picture to build is `.softfield/cards/f296-mockup/code-lines.html`, "F296's page · Behind it", Proposed.
- `tickets.code_added` and `tickets.code_removed` hold each merged ticket's code lines (NULL when not counted).
- Add `code_lines(conn, project)` to `factory_dashboard/queries.py` as D3 says; the other pages of this card read it too.
- The fold's line comes from `gists` in `factory_dashboard/milestones.py` (`cost`); the fold is `<details id="results">` in `factory_dashboard/templates/milestone.html`, its rows the `dl.kv` there.
- The bar inside follows `.spend` in `factory_dashboard/static/dashboard.css`: the rules' ink, removed as `var(--ghost)`, no status colour.

### Done when
- `code_lines` gives a milestone's full key its tickets' summed (added, removed); a milestone whose tickets are all NULL isn't in it
- a milestone with tickets +92 −13 reads "code +79 lines" after its cost on the fold's line, and "+92 −13, net +79" in a "Code lines" row inside
- a net below zero reads "−40 lines", with the minus sign `−`
- a milestone with nothing counted shows neither, and its fold line is what it was
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
