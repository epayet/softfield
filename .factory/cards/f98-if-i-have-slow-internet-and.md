# Milestone F98: A pressed button shows it is sending, and the same press is taken once

> **State:** ready · **Priority:** 6 · **Area:** factory
> Planted by the owner on 2026-10-10.

## Notes
If I have slow internet and I click plant it looks like nothing is happening. I had an issue where I planted the same thing multiple times. Add some kind of loading state to the button to be clear

The owner, 2026-10-27: "Same for things like remove or other buttons."

## Plan (lead, 2026-10-27)
- **Why a press looks like nothing:** every button that asks the runner posts to `/requests` with htmx. Plant (`#plant` in `factory_dashboard/templates/planning.html`) changes nothing until the answer comes back, and only then empties the box; on a slow connection both Plant buttons still work meanwhile, so each press is a new request and a new card (`add_request` in `runner/metrics.py`: "asking twice is two requests"). Remove seed (`#drop-seed` in `thread.html`), Save, Cancel it, Dismiss, Send, Send back, Accept ADR, Queue it are the same. A few already show something of their own (Pause, Archive, Sign off, the reserve lever, Approve plan, Reject, a blocked ticket's two buttons); the board's Send and the Projects page's order use `fetch` and say "Sending…" already.
- **One rule for every button, in one place** (D1), not one fix per button: the next button added gets it too.
- **The server takes the same press once** (D2): a press that was stored but whose answer was lost (a phone between networks) can be pressed again safely. This is what makes "press again" honest.
- Mock-up: `.factory/cards/f98-mockup/pressed-buttons.html`.
- Tickets: `f98-01-same-press-taken-once` (lead: `factory_dashboard/requests.py` is protected), then `f98-02-pressed-button-sends` (developer, UI).

## Decisions
- **D1: a pressed button shows it is sending,** from the press until the answer, on every page, from one listener in `factory_dashboard/templates/base.html` on htmx's `beforeRequest` / `afterRequest` for a POST to `/requests`. The pressed button (a form's submitter, else the element itself) takes the class `sending`: disabled, a dashed hazard edge, its label replaced by its `data-sending` word ("Planting…", "Removing…"; "Sending…" when it has none) and a hazard belt crawling under it (`--sending-belt`, a new token in `dashboard.css`; still under `prefers-reduced-motion`). Every other submit button of the same form is disabled and its text boxes read-only. A button a page already removes or replaces on press is left to its page.
- **D1 failure:** an answer that is an error, no answer within 30 s, or a lost connection gives the button back with its label and writes, in the request's target, "Didn't hear back from the factory. Your note is still here: press again, it won't be planted twice." (for a button with no text, "…press again"), in `--fail`. The owner's words stay in the box.
- **D1 success:** each page goes on as today (Coming, on its way, the thread redrawn).
- **D2: the same press is taken once.** `POST /requests` whose project, kind, subject and value equal the project's most recent request, stored less than 60 s before, stores nothing and answers with that request's row, as if it had just been stored. Only the most recent one counts, so Pause, Resume, Pause stays three requests. The console (`softfield` commands) is unchanged: asking twice there is still two requests.
