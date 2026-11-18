# Milestone F265: Planning's top tiles refresh by themselves

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-18.

## Notes
The factory now section in planning doesn't seem to auto refresh ?

From the code: right. On `/planning`, only Coming (`#live-desk-coming`) and the desk (`#live-desk`) poll every 5 s. The two tiles above them, The factory now (`#factory-now`) and The lead's window (`#lead-window`), sit in `#tiles` outside every poll: f19-01 left them out on purpose ("not the `#plant` form, not `#tiles`") without saying why, and F32 D2 noted the lead's window "doesn't refresh itself". So what's running, "Writing now … 2 min in", the replies in line and both gauges stay as they were when the page opened.

The owner, 2026-11-18: "It's the same for the answers wanted the orange dashes stay even though it's been approved or archived since. Same with the lead reply. The lead replied already but the box was still orange until I refresh. Be careful of not disturbing current typing with auto refreshes"

From the code: the desk does poll, and the server has no cache (a reload shows the truth, as the owner saw), so the poll was held back in the browser. `window.liveIdle()` (`factory_dashboard/templates/base.html`) holds every live part:
- for **10 s after any scroll**, of the page or of anything inside it. On a phone you scroll the desk all the time to read it, and coming Back from a proposal or a thread restores the scroll position, which counts as a scroll. Each scroll starts the 10 s again, so a desk you keep scrolling never refreshes;
- while text is selected, a field has focus or holds unsent text, or a fold holding a field is open: these are right, they protect what's being typed;
- and when a hold ends, nothing catches up: the next try is the next 5 s tick, held again if you scroll in between. Nothing on the page says it is held.
Which of these held the owner's desk isn't certain from the code alone; f265-02 reproduces it in a browser first.

The owner, 2026-11-18: "the board tickets also don't refresh on the board page, i had to refresh the page"

From the code: the board follows itself (F209, `factory_dashboard/static/board.js`): every 10 s, and on coming back to the page, it fetches itself and swaps what changed. It skips a turn while a card is dragged, moves wait to be sent, the ⋯ menu is open, or `liveIdle()` says no, so the same 10 s scroll hold stops it. On a phone the board is scrolled constantly, its stages sideways too, so a 10 s check lands inside a hold nearly every time. Its plate line still reads "refreshes every 10 s" while held by liveIdle: only unsent moves and a failed fetch change those words.

## Expected outcome
On `/planning`, the two tiles and the desk keep up by themselves: a job starting, a reply landing, an approval or an archive shows within about 5 seconds, without a reload, and without ever touching what the owner is typing. Coming back to the page, it shows the truth at once.

## Done when
- A job that starts or ends while `/planning` is open shows in The factory now within a poll.
- The lead's window shows a new reading (percent, "read at", reset) within a poll.
- The page still makes one request per poll for the desk and the tiles together; a note half typed in the Plant box is never touched.
- Scrolling the desk on a phone holds the refresh for about 2 s after the scroll stops, not 10 s, and the desk catches up as soon as it stops.
- Coming Back to `/planning` after Approve or Archive on another page shows the item gone (or on its way) at once, not after a reload.
- A lead reply that lands while the owner reads the desk takes the dashed orange off its box within a poll.
- Typing anywhere (the Plant box, a comment, a reply) is never redrawn: the hold stays for typing, a selection and an open editor.
- On `/board`, a ticket that moves (a card's count, a stage, what's at work) shows within about 10 s of the owner stopping scrolling, and its plate line says when the refresh is held and why, instead of "refreshes every 10 s".

## How to test
Open `/planning` on the phone while the runner is between jobs. When the next job starts, The factory now changes from "Nothing running right now." to "Running …" without a reload; "… min in" grows as you watch. Then open a card in Your answers wanted, approve its plan, and go Back: the card shows on its way at once. Scroll the desk while a reply is being written: once you stop, the box loses its orange dashes within a few seconds. Type half a note in the Plant box and wait: the note stays.

## Decisions
- **D1 Ride the desk's poll.** `#live-desk` already fetches the whole `/planning` page every 5 s and keeps only `#desk`. It also picks the two tiles out of the same answer (`hx-select-oob="#factory-now:innerHTML,#lead-window:innerHTML"`), as the Overview's `#live-needs-you` does for Now, Queue and the allowance. No new wrapper, no new request (F19's rule: one request per poll, not one per part).
- **D2 Buttons keep their own answers.** The wrapper's children (Dismiss, Approve, Try again, Set aside) post to `/requests`; they must inherit neither `hx-select` nor `hx-select-oob`, so the wrapper's `hx-disinherit` names both.
- **D3 It pauses with the desk.** The tiles wait while the owner types, as the desk does: a few seconds late is fine, a wiped note isn't.
- **D4 No mock-up.** Nothing on the page moves or changes look: the tiles and the desk show what they already meant to, kept current.
- **D5 Hold only for what a redraw would lose.** `window.liveIdle()` keeps its holds for typing (a focused field, unsent text, an open fold holding a field) and a selection. The scroll hold drops from 10 s to 2 s after the last scroll: long enough not to jump the page under a finger, short enough that a desk being read still refreshes. It is one function in `base.html`, shared by every live page (the Overview, the line, the board, threads, proposals), and they all gain the same.
- **D6 Catch up when the hold ends.** `base.html` sends one `live-resume` event on `document` when liveIdle goes from false to true (checked every second), and when the page comes back (`pageshow` restored from the browser's back cache, and `visibilitychange` to visible). Each htmx poll adds `live-resume from:document` to its `hx-trigger` (the planning page's two wrappers here; other pages may follow); the thread page's own `setInterval` poll also runs once on it.
- **D7 Lead first, test-first.** f265-02 is the lead's: the cause is not proven from the code, and `liveIdle` is shared by every live page. It starts by reproducing the owner's three cases in a browser (Back after Approve, scrolling while a reply lands, an archive), so the fix is shown to change the failing case.

- **D8 The board joins the catch-up.** `board.js`'s `follow` also runs on `live-resume`, so the board catches up when the scroll stops, not at its next 10 s tick. Its plate line (`sayFresh`) gets one more state: "Refresh held while you scroll or type" while `liveIdle()` held the last turn, back to "refreshes every 10 s" once a turn goes through. Unsent moves and a failed fetch keep their words and come first. Wording in an existing line, so no mock-up.

## Tickets
1. `f265-01-tiles-refresh` (developer): the two tiles come from the desk's poll.
2. `f265-02-live-parts-catch-up` (lead, after 01): the shorter scroll hold and the catch-up, test-first from the owner's cases.
3. `f265-03-board-catches-up` (developer, after 02): the board follows on `live-resume` and says when it is held.
