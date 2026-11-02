# Milestone F133: Each project gets its own card letter, and the factory/product area goes

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-15.

## Notes
From the terminal session of 2026-10-14 (ADR 30). The owner asked whether milestone
names can clash between projects, and how to tell a new project's M1 from Coucou's.

Today: the database keeps them apart (`milestones`, `tickets`, `planner_threads` are unique per
project), and each repo has its own cards, tickets and tags. But a card's key comes from its
"area" (`planner.SERIES = {"factory": "f", "product": "m"}`, `planner.next_key`), a rule from when
Coucou and the factory shared one repo: every new product project starts at M1, like Coucou
(test-factory-hello's first card is m1-uv-run-hi). In the shared places (the factory-wide top bar
and Projects page name the project already; the planned factory-wide Overview, the Line, Jobs,
Runs), in conversation, and in ticket ids and commit trailers (`Task: m1-01-…`), "M1" no longer
says which project.

Proposed: each project has its own series letter(s) in `.softfield/project.toml`
(`[project] series = "h"`); `softfield init` picks one no registered project uses, from the
project's name (hello → h), and the setup session (docs/bootstrap.md) can change it; `next_key`
uses it. Softfield keeps `f` and Coucou keeps `m`: nothing is renumbered. The factory/product
"area" goes, since each repo is one project now (ADR 19 2b foresaw it: "the area becomes the
project"); check what still reads `area` (the board's colours, plants' `area`, milestone docs'
**Area:**). Card keys, ticket ids and commit trailers are then unique on the machine.

The owner: leave test-factory-hello as it is (m1).

### From F155: We don't need the product vs factory on the board. But in… (merged by the lead on 2026-10-27)
We don't need the product vs factory on the board. But in the reports it's helpful

What was said on F155's thread:
The owner planted: no product vs factory split on the board, but it helps in the reports. Later message: remove the whole 'for Mum' thing and the area splits and filters on the board. Nothing was answered on F155. Still open: whether the board keeps a Bugs filter or loses every filter.
