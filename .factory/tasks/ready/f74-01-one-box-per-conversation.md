---
id: f74-01-one-box-per-conversation
milestone: f74-when-i-reply-to-a-your
difficulty: 3
depends_on: [f63-01-desk-order]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A thread the owner has written on keeps one box, in "Your answers wanted", dashed orange until the lead's reply is stored; Coming holds only plants, as "Coming seeds".

### Context
Read `.factory/cards/f74-when-i-reply-to-a-your.md` (Why it happens, D1–D5), then `coming`, `_answers_wanted`, `_seeds`, `_acted_on`, `_open_proposals` (its `on_its_way` items are the example to follow) and `desk` in `factory_dashboard/planning.py`.
- `coming()` keeps only its plant rows; the group's name becomes "Coming seeds". The thread part (the `planned`, `owners_last`, `asked` queries) moves to `_answers_wanted()`.
- `_answers_wanted()` lists, once each and in thread order: threads whose latest message is the lead's (today's rows), plus threads the owner is waiting on: an open `plan_message` request names the card, or the latest message is the owner's and an open planner job's subject (`card#…`) names it. Those waiting ones are `on_its_way=True`, words `f"waiting for the lead · {next_reply}"` (`_next_reply` with `_held(conn, project_id, now, card)`, as `coming()` does today), and are listed even when the thread is archived or doesn't exist yet (a seed's first message: its title from `_card_titles`).
- `_seeds()` leaves out a card with an open `plan_message` request naming it.
- `desk()` needs `project` and `now` for `_answers_wanted()` now; pass them.
- The template's Coming heading reads the group's name (`coming.name`) instead of the literal "Coming"; nothing else in it changes.
- Tests: the Coming tests about threads (`test_a_thread_with_open_plan_message_request_shows_in_coming`, `..._open_planner_row_shows_in_coming`, `..._both_open_request_and_planner_row_shows_once`, `test_coming_skips_a_job_whose_run_has_stopped_beating`, `test_a_reply_parked_for_a_limit_says_which_and_until_when`'s Coming line, `test_after_the_request_is_done_and_the_lead_replies_the_thread_leaves_coming`, `test_a_first_message_on_a_card_with_no_thread_shows_in_coming`, `test_after_the_leads_reply_the_thread_moves_to_answers_wanted`) become the same checks on the `answers` group's dashed item. Keep their setups.

### Done when
- a thread whose latest stored message is the lead's, with an open `plan_message` naming it: one item in the `answers` group, dashed (`on-its-way-item`), "waiting for the lead"; no `desk-coming` on the page
- the same thread after the request is done and the owner's message stored, with an open planner job: still one dashed item in `answers`, same link
- after the lead's reply is stored: the item is solid and counted in the Planning tab's count
- an open `plan_message` on an idea card with no thread: the card is a dashed item in `answers` and not in `seeds`
- an open plant request: `desk-coming` shows it under the heading "Coming seeds", and only it
- the Planning tab's count and the Overview's Needs you don't change when a message is sent
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
