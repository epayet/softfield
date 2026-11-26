---
id: f299-01-plant-says-who-suggested
milestone: f299-i-want-to-be-able-to-4
difficulty: 3
depends_on: []
files:
  - runner/requests.py
  - runner/planner.py
  - runner/milestone.py
  - factory_dashboard/milestones.py
  - factory_dashboard/stacks_routes.py
  - .softfield/cards/f258-runner-when-a-third-fix-ticket.md
  - .softfield/cards/f260-the-before-pictures-should-be-taken.md
  - .softfield/cards/f269-tests-factory-dashboard-test-jobs-py.md
  - .softfield/cards/f270-tests-runner-test-shots-py-waits.md
  - .softfield/cards/f271-test-a-change-that-isnt-stored.md
  - .softfield/cards/f292-the-line-stopped-strip-and-needs.md
  - .softfield/cards/f295-runner-requests-py-s-forget-project.md
  - .softfield/cards/f296-show-each-milestone-s-net-code.md
  - .softfield/cards/f304-simpler-tests-runner-test-backup-py.md
  - .softfield/cards/f201-ticket-pages-render-markdown.md
  - .softfield/cards/f202-while-main-is-red-hold-tickets.md
  - .softfield/cards/f294-this-was-a-suggestion-card-is.md
  - .softfield/cards/f303-from-a-factory-suggestion-add-a.md
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_planner.py
  - tests/runner/test_milestone.py
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_stacks_routes.py
agent: lead
area: factory
---

## Goal
Every planted card records where its idea came from (`**Origin:**` owner, review, lead or projects), which review (`**From:**`) and whether the owner edited it (`**Edited:**`), as fields in its header, set from the plant request and read back by `milestone.card`.

## Context
Read "What we know", "Settled with the owner" and D1, D2, D3 and D5 in `.softfield/cards/f299-i-want-to-be-able-to-4.md`.
- `runner/planner.py`: `seed_card` takes the origin (owner by default) and writes the fields on the first header line, after `**Area:**`; a helper turns the plant value into them (`from: "fN/k"` → review and `FN`; `from: "projects"` → projects; `edited: true` → yes; anything else → owner, never refused).
- `runner/requests.py`, `_plant` and `_seed`: pass the origin to `seed_card`; an approved general-thread seed is `lead`, and `_seed` stops returning "from the general thread's pN". The commit message stays "FN planted by the owner".
- `runner/milestone.py`: `Card` gains `origin` ("owner" when absent), `origin_from` and `edited`, read with regexes beside `CARD_RESERVE_RE`. Check the other header readers (`_CARD_STATE_RE`, `_CARD_AREA_RE`, `milestone_after`) still read a header that has the new fields.
- `factory_dashboard/milestones.py` `idea_vals`: the text is the idea alone, without " From FN's review."; keep `from`. The plate's planted state (`v.get("from") == idea.id`) must keep working.
- `factory_dashboard/stacks_routes.py` `plant_value`: adds `"from": "projects"`.
- The thirteen cards in `files:` (one-off, on main): add the fields to the first header line and change nothing else but what follows. Review, edited no, with the tail sentence dropped from Notes: F258 (F164), F260 (F222), F269, F270, F271 (F71), F292 (F97), F295 (F273), F296 (F286), F304 (F290). Review, edited no, with the "From docs/backlog.md …" line dropped: F201 (F159), F202 (F80). Review, edited yes, Notes untouched: F294 (F273), F303 (F290). Leave F164 alone.

## Done when
- a Plant box note's card has `**Origin:** owner` and no From or Edited
- a plant with `from: "f286/3"` gives `**Origin:** review · **From:** F286 · **Edited:** no` and Notes holding the text alone; with `edited: true` as well, `**Edited:** yes`; `from: "projects"` gives `**Origin:** projects`; an approved general-thread seed gives `**Origin:** lead`; an unknown `from` gives `**Origin:** owner`
- `milestone.card` gives origin, origin_from and edited for such docs, and `owner`, "" and false for a doc without the fields; state, area and fast lane read as before
- `idea_vals`' text has no "From …'s review." and a planted idea's plate still shows Planted with its card
- the thirteen cards carry the fields, and no card in `.softfield/cards/` other than F164 ends a note with "From F…'s review."
- the listed `tests:` pass, and the new ones fail without the change
- all gates pass
