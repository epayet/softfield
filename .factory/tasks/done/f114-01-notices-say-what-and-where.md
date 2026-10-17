---
id: f114-01-notices-say-what-and-where
milestone: f114-i-want-to-be-notified-only
difficulty: 4
depends_on: []
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/live.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The `/live` partial gives each thing that notifies the owner a title, a body and the page to open, worded from the item's kind and its card's title.

### Context
Read `.factory/cards/f114-i-want-to-be-notified-only.md` (D1: its table is the wording to build), then `needs_you` and `_live_context` in `factory_dashboard/overview.py`, `factory_dashboard/templates/_partials/live.html`, and `_card_titles`, `_thread_title` and `_open_proposals` in `factory_dashboard/planning.py`. Follow the worked example in `tests/factory_dashboard/test_overview.py`: `test_a_lead_reply_shows_once_in_the_desk_entry` (its helpers store a lead's reply and read `#live-facts`).
- Add a function `notices` to `factory_dashboard/overview.py`: for every open need (the list `_live_context` already has as `open_needs`), its id mapped to `{"title", "body", "link"}`. `_live_context` passes it to the template, and `#live-facts` carries it as JSON in a new attribute, `data-notices`.
- An owner item's subject isn't on `Need` today: carry it there, or read the rows again. For `planning` it is the thread's card (`f7`, or `general`); for `signoff` and `review-stop` it is the milestone's key, short or full: use `short_key` from `runner/tasks.py` for the title and the link.
- The count of proposals to review is the number of desk items `_open_proposals` gives for that card that are not on their way; with none, the body is "Your answer is wanted".
- A lead's job that failed is a `planning` item whose stored text starts with "The lead couldn't answer".
- A card with no title in the database shows its key.
- `factory_dashboard/planning.py` imports from `factory_dashboard/overview.py` at module level: import from it inside the function, as `_live_context` does.
- Leave `data-needs`, `notify` and `factory_dashboard/static/notify.js` as they are: the next ticket moves the page to `data-notices`.

### Done when
- a lead's reply on a card with two open proposals: its notice is titled "The lead replied: <the card's title>", says "2 proposals to review" and links to `/planning/<card>`
- a lead's reply with no proposal: "Your answer is wanted"; one proposal: "1 proposal to review"
- a failed lead's job: titled "The lead couldn't answer: <the card's title>", body "Send your message again"
- a reply on the general thread is titled "The lead replied: General" and links to `/planning/general`
- an open `signoff` item: "Ready for your sign-off: <the card's title>", body "Reviewed, waits for you", link `/planning/<short key>`
- an open `review-stop` item: "The review stopped: <the card's title>", its stored text as the body, link `/planning/<short key>`
- items of kind `adr`, `blocked`, `escalated`, `reserve` and `five-hour`, the stopped runner and the idle queue: the title D1's table gives, the item's text as the body, link `/`
- every link keeps the page's project, as the other links of the partial do
- `data-notices` has exactly the ids `data-needs` has
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 8342
gate_failures: ['mypy']
tokens: 9123891
```
