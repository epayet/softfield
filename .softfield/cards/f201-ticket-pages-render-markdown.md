# Milestone F201: Ticket pages, card notes and lead replies render code, bold and links

> **State:** ready · **Area:** factory
> From docs/backlog.md (f159-review), written by the lead on 2026-11-02.

## Notes
A ticket page's parsed Goal, Done when and notes show markdown as typed (`` `git show …` ``, `**not from the code**`): the dashboard has no markdown rendering. If it ever gets one (cards' docs would want it too), use it here; until then, plain text is honest. Stays: waits for a markdown renderer (bug-30 grows the sheet's).

## What we know (2026-11-16)
- The renderer it waited for is planned: F216, A shorter, consistent review page, has `_to_html` in `factory_dashboard/milestones.py` learn `` `code` ``, `**bold**` everywhere and `http(s)` links (its D12, ticket f216-02). Today it knows only `- ` bullets and bold inside them.
- `factory_dashboard/templates/ticket.html` prints the parsed Goal, Done when and notes as plain text; the card's note is plain on its page (`milestone.html`) and its thread (`thread.html`); the lead's words on a thread go through `_text_with_links` in `factory_dashboard/merges.py`, which links references but leaves backticks as typed.
- The dashboard already styles `code` (`dashboard.css`, line 83): no new CSS or token is needed.

## Outcome
Wherever the dashboard shows the lead's or the owner's written words on a ticket or a card, backticks show as code, `**x**` as bold and an `http(s)` link as a link, from one set of rules shared with the review sheet.

## Done when
- a ticket's page shows its Goal, Done when and notes with code, bold and links rendered
- a card's note shows them rendered on its page and its thread, its line breaks kept
- the lead's replies on a thread show code and bold rendered, their card and ticket links kept
- `<script>` or any HTML typed in any of them still shows as typed

## Decisions
- **D1. One set of rules.** The inline part of `_to_html` (after f216-02) becomes `inline_html(text) -> Markup` in `factory_dashboard/milestones.py`, used by `_to_html` itself and registered as the template filter `md` in `factory_dashboard/app.py`. It escapes first; links only for `http://` and `https://`, the text alone otherwise.
- **D2. Inline only, the structure stays.** The ticket page keeps `parse_ticket_body`'s paragraphs and lists; only their text goes through `md`. A note keeps `white-space: pre-line`, so its lines and `- ` bullets stay as typed.
- **D3. Where `md` goes:** the parsed `#goal` panel of `ticket.html` (not its `<pre>` fallback); the note and each ticket's goal on the card's page; the note on the thread.
- **D4. No new look.** `code` and `strong` take the dashboard's existing styles: the mock-up `.softfield/cards/f201-mockup/ticket-and-note.html` shows the change is text only.
- **D5. The lead's words on a thread** get code and bold in `_text_with_links`, before references are linked, so a ticket in backticks is a linked code chip. No markdown links there (a reference inside an `href` would break the page). The owner's messages stay plain.
- **D6. Order and who builds.** 01 waits for f216-02 (the rules) and f216-03 (it rewrites `milestone.html`). 01 developer: a split, a filter and template edits, with `_to_html`'s tests as the example. 02 lead: regex substitutions on escaped HTML, in front of the reference links, where a mistake breaks every thread.

## Before and after
- `/tickets/f216-02-findings-costs-and-markdown`
- `/milestones/f201-ticket-pages-render-markdown`
- `/planning/f201`

## Later
- The board's at-work line and the Tickets list show one-line titles; they could take `md` too if backticks show there.

## Tickets
| # | ticket | who | difficulty | after | decisions |
|---|---|---|---|---|---|
| 01 | ticket-and-note-render-markdown | developer | 3 | f216-02, f216-03 | D1, D2, D3, D4 |
| 02 | lead-replies-render-code | lead | 3 | 01 | D5 |
