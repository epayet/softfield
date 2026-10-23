---
id: f158-01-card-says-what-its-about
agent: developer
milestone: f158-milestones-don-t-show-me-their
difficulty: 3
depends_on: [f90-01-seed-shows-its-note]
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A card's page (`/milestones/<key>`) says what the card is about right under its header: the Outcome and Done when from the card's doc, else the owner's note, and the seven empty review sections wait as one line until the review writes them.

### Context
Read `.factory/cards/f158-milestones-don-t-show-me-their.md` (Why it happens, D1–D3) and build the picture in `.factory/cards/f158-mockup/card-page.html` (Proposed). Then `milestone_detail` in `factory_dashboard/milestones.py`, `factory_dashboard/templates/milestone.html`, and in `factory_dashboard/planning.py` `_repo` and the function `thread_page` uses to read a card's `## Notes` for `#note` (f90-01 added it): reuse it, don't copy it.
- The doc is `milestone_file(repo, "cards", key)` (`runner/tasks.py`): cards live in `.factory/cards/`. f90-01's ticket named the folder `milestones`; if its notes reader looks there, point it at `cards` too, so both pages find the real docs. Its Outcome and Done when come from `milestone_doc` (`runner/milestone.py`); shown with `_to_html`, as today.
- No checkout or no doc: the stored `milestone.outcome` and `done_when`, as today.
- `<section id="about">` right after `#card-head`, before `#grew`, headed "What it's about", in the mock-up's plate style (plate header, hazard stripe, corner ticks: ink, rules and stripe only, never a status colour). New CSS goes beside the card page's rules in `dashboard.css`, from its tokens.
  - With an Outcome: "What it will do" and the Outcome, then "Done when" if there is one, then the note in a folded `<details>` "Your note" (summary min-height 44px), when there is a note.
  - No Outcome, a note: "Your note" open, then "The lead writes what it will do when it plans the card."
  - Neither: "Nothing written about it yet." and a link to its thread (`/planning/<thread>`).
  - The note escaped, `white-space: pre-line`, never `| safe`.
- The old `#outcome` section goes.
- No sign-off sheet stored (`signoff_html` empty): the seven sections from `#what-changed` to `#clogged` are replaced by one `<section id="review-wait">`: "The review" and "comes when the last ticket is done: what changed, how to test it, decisions for you, what next." Any sheet stored: the sections as today, and no `#review-wait`. `#review` (Sign off) is untouched.
- Tests build the card's doc in the test project's repo folder, as the thread tests in `tests/factory_dashboard/test_planning.py` do for f90-01.

### Done when
- a card whose doc has `## Outcome` (with no stored outcome) shows its Outcome in `#about`, before `#grew`, and its note in a folded "Your note"
- a card whose doc has only `## Notes` shows the note open and "The lead writes what it will do"; one with neither shows "Nothing written about it yet." and its thread's link
- the docs are read from `.factory/cards/` (a test puts the doc there)
- a project whose repo isn't a folder here shows the stored outcome, and the page renders
- with no sign-off sheet: `#review-wait`, and none of `#what-changed` … `#clogged`; with a sheet: those sections, no `#review-wait`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3900
gate_failures: []
tokens: 9714446
```
