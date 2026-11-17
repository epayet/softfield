# Milestone F133: Each project gets its own card letter, and the factory/product area goes

> **State:** ready · **Area:** factory
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
project's name (hello → h), and the setup session (runner/instructions/bootstrap.md) can change it; `next_key`
uses it. Softfield keeps `f` and Coucou keeps `m`: nothing is renumbered. The factory/product
"area" goes, since each repo is one project now (ADR 19 2b foresaw it: "the area becomes the
project"); check what still reads `area` (the board's colours, plants' `area`, milestone docs'
**Area:**). Card keys, ticket ids and commit trailers are then unique on the machine.

The owner: leave test-factory-hello as it is (m1).

### From F155: We don't need the product vs factory on the board. But in… (merged by the lead on 2026-10-27)
We don't need the product vs factory on the board. But in the reports it's helpful

What was said on F155's thread:
The owner planted: no product vs factory split on the board, but it helps in the reports. Later message: remove the whole 'for Mum' thing and the area splits and filters on the board. Nothing was answered on F155. Still open: whether the board keeps a Bugs filter or loses every filter.

## Before and after
- `/board?project=travel-companion`
- `/milestones/f133-each-project-has-its-own-series`
- `/planning/f133`

## Plan (lead, checked against main 2026-11-14)
- **What "area" does today, from the code:** it picks a new card's letter (`SERIES`, `next_key` in `runner/planner.py`); it is a card header line (`**Area:**`, read by `card` in `runner/milestone.py`) and a bug ticket's required `area:` (pre-flight, `runner/tasks.py`); the runner writes it to the `milestones` and `tickets` rows; the board colours each card's edge by it, labels it, filters by it and explains it in the legend ("product (for Mum)"); the card page has an Area row and a thread's page stamps it beside its title (`_header`, `factory_dashboard/thread.py`). On travel-companion's board today, "F7 factory a map view of my trips" and "M2 product Stamps and the Stampu seal" sit side by side: the word no longer means anything there. And M1 now names a card in Coucou, travel-companion, coaster-ranker and the test-factory-hello projects: coaster-ranker's cards run M1 to M12.
- **ADR 30 already settled it** ("a card's area becomes its project", amending ADR 19 2b), so dropping `area:` from a bug ticket needs no new ADR: `runner/instructions/task-format.md` follows it.
- **Builds on F171, Each card once on the board:** its ticket `f171-04-plant-takes-the-projects-area` is done: `project_area` in `runner/planner.py` reads `area` under `[project]`, and Softfield's project.toml says `area = "factory"`. f133-01 swaps both for `series`.
- **The branch was rebuilt on main by f139-03** on 2026-11-14, but one file stayed at its old place, `.factory/cards/f133-mockup/board.html` (the mock-up now lives at `.softfield/cards/f133-mockup/board.html`). Approve refuses a plan that changes anything outside the drafts' folders, and a planning job can't delete a file: it is removed by a commit on `plan/f133` before the approval.
- **Waits on what else changes the same code:** F222's tickets take the priority out of the same card headers, pages and runner files (f133-03 after f222-03, f133-04 after f222-04); F236's moves the registering from `init` to `softfield create` (f133-02 after f236-01).
- Tickets: `f133-01-cards-take-the-projects-series` (lead, runner), `f133-02-init-picks-a-series` (lead, runner and the setup instructions), `f133-03-board-without-areas` (developer, dashboard), `f133-04-area-retires-from-the-runner` (lead, runner and the task format). 02 and 04 wait for 01; 04 waits for 03 too, so the board never shows a card without its area while it still reads one.
- Mock-up: `.softfield/cards/f133-mockup/board.html` (travel-companion's board, a card page and a thread's title, Today and Proposed).
- After it lands: `series = "t"` goes into travel-companion's `.softfield/project.toml` and `series = "c"` into coaster-ranker's (one line each, in their own repos, which no ticket here can write): their next cards are T1 and C1, and every key already given stays.

## Decisions
- **D1: a project's series is `series` under `[project]` in its `.softfield/project.toml`:** one to three lowercase letters, never `bug`. Softfield's says `f`. Missing or not valid, it is `m` (Coucou and the test-factory-hello projects stay as they are). `project_series` replaces f171-04's `project_area`, and `series` its `area` line: an `area` left in a project.toml is ignored.
- **D2: `next_key(repo, taken)` takes no area:** it reads the series from the repo (D1) and counts only that series' keys. A plant's or a seed's `area` is ignored, never refused: the review's and the weekly report's idea plates send one (`f164-03`, `f59-04`). Keys already given are never renamed.
- **D3: `softfield init` writes the series it picks** into the new project.toml: the name's first letter, else its first two letters, else the first free letter of a–z, skipping `f`, `m` and any series a project in the factory uses (read from each project's repo, `projects.repo`; missing counts as `m`; since F236 a project joins the factory at `softfield create`, after `init`). The setup session may change it before the first card, which is `<series>1-<slug>` (`runner/instructions/bootstrap.md`).
- **D4: area goes from new cards and from the runner:** `seed_card` writes no `**Area:**`; `Card` has no area; the runner stops writing the `area` columns (they stay in the database, unread). An old doc's `**Area:**` line and a ticket's `area:` are read without complaint and ignored, whatever they say; `_card_marked` still writes the fast lane after an old doc's Area. A bug no longer needs `area:` to pass pre-flight.
- **D5: the board and the pages show no area:** every card's edge is the hazard yellow (what Softfield's board shows today); a bug keeps its striped edge and "bug" label; the kind filter is All and Bugs, beside the developer's view lever, which stays; the legend loses "factory" and "product (for Mum)". The card page loses its Area row, and a thread's title its "factory" stamp. The bug filter stays (the owner, 2026-10-27, from F155: "We don't need the product vs factory on the board").
- **D6: the reports keep their product and factory split** (the owner, 2026-10-27: "in the reports it's helpful"). A milestone review's "What next" still gives product and factory suggestions (`REVIEW` in `runner/prompts.py`), its idea plates still plant a factory idea in Softfield and a product idea in the reviewed project (`factory_dashboard/milestones.py`, F164), and the weekly report's "Ideas for the factory" and "Ideas for <project>" do the same (`f59-04`, F59). None reads a card's area, so no F133 ticket touches them.
