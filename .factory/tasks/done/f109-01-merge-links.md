---
id: f109-01-merge-links
milestone: f109-when-plans-get-merged-i-need
difficulty: 4
depends_on: [f22-01-archive-at-the-bottom]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On a card's thread page, a card merged away links to the card that took its notes, and that card links back to every card merged into it.

### Context
Read `.factory/cards/f109-when-plans-get-merged-i-need.md` (D1 to D4, D6). In `runner/planner.py`: `merged_card` writes the heading the links are read from, `card_notes` moves headings down in a chain, `cards` lists the cards on main. In `factory_dashboard/planning.py`: `thread_page`, `_header`, `_repo` (the project's checkout, or None) and `_known_cards`. In `factory_dashboard/templates/thread.html`: `<header id="card">` and the lead's message without points.
- The heading, in a card's doc in `.factory/cards/`: `### From F107: <title> (merged by the lead on 2026-10-13)`, with three to six `#`, "the lead" or "the owner". The doc it sits in is the kept card; `F107` is the merged one.
- In the header, under the title: on the merged card's thread, one `a.merged-into` per card it went into, "Merged into F95, <F95's title>" to `/planning/f95`, with the date; on the kept card's thread, one `a.merged-here` per heading, "Merged here: F107, <the heading's title>" to `/planning/f107`, with the date. Each link keeps `{{ q }}` and is at least 44px high.
- A merged card has no `milestones` row left, so `_header` gives its bare key: show the heading's title instead (the latest merge's).
- Follow `test_a_merge_whose_card_left_main_asks_nothing` in `tests/factory_dashboard/test_planning.py` for a checkout with docs (the `checkout` fixture).
- **In the tests, build the kept card's doc with `merged_card`, never a heading typed by hand: the reader must follow the writer.**

### Done when
- with F95's doc holding F107's merge, `/planning/f107` has a link to `/planning/f95` saying "Merged into F95" and F95's title, and its `h2` shows F107's title from the heading
- `/planning/f95` has a link to `/planning/f107` saying "Merged here: F107" and that title
- a kept card with two merges lists both; a key merged into two cards (F64 into F13 and F42) lists both on its thread
- a chain: F107's notes moved from F95 into F10 (the heading one level down in F10's doc) gives `/planning/f107` a link to F10, and `/planning/f10` links to both F95 and F107
- a key that has a card again on main says "An earlier F73 was merged into F43" and keeps the card's own title
- a lead message without points whose text holds `/planning/f95` shows it as a link; `<b>` in that text still shows as text, and an owner message holding the path has no link
- a card with no merge, the general thread, and a project with no checkout show no such links
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 6199
gate_failures: ['stopped']
tokens: 10134994
```
