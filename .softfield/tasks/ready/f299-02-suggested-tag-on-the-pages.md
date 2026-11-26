---
id: f299-02-suggested-tag-on-the-pages
milestone: f299-i-want-to-be-able-to-4
difficulty: 2
depends_on: [f299-01-plant-says-who-suggested]
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/templates/thread.html
  - factory_dashboard/milestones.py
  - factory_dashboard/thread.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_thread.py
---

## Goal
A card the factory suggested shows who suggested it, and whether the owner edited it: a tag on its board card, and "<who> suggested" in place of "Your note" on its page and its thread. The owner's own cards look as today.

## Context
Read D3 and D4 in `.softfield/cards/f299-i-want-to-be-able-to-4.md`. The picture to build is `.softfield/cards/f299-mockup/suggested-by.html`, its Proposed.
- `runner/milestone.py` `card()` already gives `origin` ("owner", "review", "lead" or "projects"), `origin_from` (`F286` for a review) and `edited` (f299-01). Read them there; don't parse the header yourself.
- `factory_dashboard/board.py`: `Card` gains `origin`, `origin_from` and `edited`, filled from `milestone_header(...)` where the card's doc is read (follow how `marked` reads the doc for `reserve`).
- `factory_dashboard/templates/board.html`, `card_link`: for any origin but owner, after the key in `card-meta`, a `card-suggested` span with the small cog SVG from the mock-up and the short form ("F286 review", "lead", "Projects page"), then " · edited" when edited; the full words in its `title`. Follow `card-growing`.
- `factory_dashboard/static/dashboard.css`: add `--suggested: var(--ink-2);` to both `:root` blocks beside the other tokens, then `.card-suggested` after `.card-growing` (dashed border, no status colour).
- `factory_dashboard/milestones.py` (`AboutDoc`, `read_card_doc`) and `factory_dashboard/templates/milestone.html`: for a suggested card, the "Your note" label and summary read "<who> suggested" ("F286's review", "The lead", "The Projects page"), with the line "a factory suggestion · you planted it on <date>", ", edited by you" when edited, and for a review a link to `/milestones/<the reviewed card's full key>#review` (`full_key`). The date is from the header's "Planted by the owner on" line.
- `factory_dashboard/thread.py` and `factory_dashboard/templates/thread.html`: the `#note` fold's "Your note" reads the same way.

## Done when
- on `/board`, a card with `**Origin:** review · **From:** F286 · **Edited:** no` shows an "F286 review" tag after its key; one with `**Edited:** yes` shows "F290 review · edited"; a card with `**Origin:** owner`, or no Origin, shows none
- the card page and the thread of a review card say "F286's review suggested" with a working link to F286's review, and "edited by you" when edited; an owner's card still says "Your note"
- `--suggested` is in both themes' tokens and `.card-suggested` uses no status colour
- the listed `tests:` pass, and the new ones fail without the change
- all gates pass (see `docs/workflow.md`)
