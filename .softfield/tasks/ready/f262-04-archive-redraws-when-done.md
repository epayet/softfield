---
id: f262-04-archive-redraws-when-done
milestone: f262-i-want-ability-to-archive-a
difficulty: 3
depends_on: []
files:
  - factory_dashboard/templates/projects.html
tests:
  - tests/factory_dashboard/test_projects.py
finding: f262-i-want-ability-to-archive-a-F2
area: factory
---

### Goal
Once the runner takes an Archive or Unarchive, the Projects page moves the project between the list and the Archived bay by itself, without a reload, as a Pause already redraws its plate (f124-04).

### Context
- The Pause redraw to follow: the last script in `factory_dashboard/templates/projects.html` (an `htmx:afterSwap` listener on `.pause-sent p.request.done` whose parent id starts `pause-sent-`), and its tests `test_the_pause_plate_redraws_when_done` and `test_a_drafted_order_on_another_plate_survives_the_redraw` in `tests/factory_dashboard/test_projects.py` (`_runner_takes` finishes a request as the runner does).
- Archive's done line lands in `#archive-sent-<name>` on the plate, Unarchive's in `#unarchive-sent-<name>` in the bay's crate. Today neither redraws: the plate keeps "Archiving…" until a reload.
- An archive moves a plate out of the ordered list (and its places' `max`) into `#projects-archived`, which may not exist yet; an unarchive does the reverse and may leave no bay. So redraw the whole `#projects-order` section from the page (`htmx.ajax` with `select`, `swap: "outerHTML"`).
- A drafted order is never lost: when `.send-order` is enabled (a place typed, not sent), don't redraw; the done line stays and a reload shows the move.

### Done when
- after Archive is pressed and the runner finishes the request, within the request's poll, coucou has no plate in `#order-form` and a crate in `#projects-archived` (closed, "Archived · 1"), with no reload
- after Unarchive is pressed in the bay and the runner finishes the request, the project's plate is back in `#order-form` with an enabled Archive button that posts `archive_project`, and with no other archived project there is no bay
- with a place typed on another plate and not sent, the archive's done line shows and the typed place and the enabled Send new order stay
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
