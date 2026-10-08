# Milestone F13: Planting idea UI feedback

> **Status: planned** (2026-10-07, with the owner, in the planning room). **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-07.

## Notes
I like the "coming" dotted box when I plant an idea and the runner will look into it next. However when I just planted the idea, the direct feedback is "the runner will plant it" or something like that. I want to see the coming box straight away without having to reload. 

Also remove the "no Claude needed" line

### From F64: It is still the case that when I plan an idea, it doesn't… (merged by the lead on 2026-10-08)
It is still the case that when I plan an idea, it doesn't go to coming and the form is still full and I have to refresh the page. Verify that this is planned for soon

## Outcome
- Pressing "Plant it" on `/planning` shows the idea in Coming at once, dashed orange, "planting at the runner's next pick", with no reload; the form is empty again for the next idea.
- The "No Claude needed" line is gone (done 2026-10-07: the line under Plant it now says "It becomes a seed card, and the lead answers it on its thread.").

## Decisions
- **D1 Re-fetch, not a new partial:** Coming already lists open `plant` requests (`coming` in `factory_dashboard/planning.py`); only the page doesn't redraw. After the request is stored, the form and Coming are re-fetched from `/planning` and swapped in, the same way f6-21 shows a sent message. No new route, no client-side copy of the card.
- **D2 Not editable:** a planted idea in Coming can't be edited (owner.md: a request stops being editable once made). Cancelling one is F14's.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | planted-idea-shows-at-once | D | 3 | – | D1 |

## Done when
- Plant it, on a phone and a display: the idea appears in Coming without a reload, and the form is cleared.
