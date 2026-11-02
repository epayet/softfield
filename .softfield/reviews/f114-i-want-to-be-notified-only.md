# Review: F114, notifications only for what needs you, one per bundle, opening its page

- **Status:** done, signed off by the owner on 2026-10-23.

## Sign-off sheet

### 1. What changed
A notification now says what it is about, with the card's own title: "The lead replied: *card*" with "2 proposals to review" or "Your answer is wanted", "Ready for your sign-off: *card*", "The review stopped: *card*", "A decision for you", and so on. A tap opens the page where you answer it: the card's conversation for a reply, a sign-off or a stopped review, the Overview for the rest. Whatever arrives in the same 5-second look is one notification ("3 things need you", their titles one per line), and a tap on it opens your desk in Planning. A finished ticket still never notifies.

The review fixed two gaps on the way: a sign-off that arrived as the queue emptied used to show only as "All work done" (now both are in one notification), and a failing check on main had stopped notifying at all (now "A check fails on main").

### 2. How to test it yourself
1. On the phone, open any dashboard page (the Board will do) with notifications allowed, and leave it open.
2. On a card's conversation, send the lead a message, then wait for the reply.
3. One notification comes, titled "The lead replied:" and the card's title, saying how many proposals it carries.
4. Tap it: that card's conversation opens.
5. While the runner merges tickets, no notification comes.
6. When a milestone's review ends with nothing else queued, one notification names both the sign-off and "All work done"; a tap opens your desk.

### 3. Left for later
- Notifications with every dashboard page closed: F142's ntfy sender does that (ADR 31), and its tickets are on the board.
- One nit in the backlog: a failed lead reply is recognised by the runner's own words (F7).
- The service worker's tap test still reads `sw.js` as text; it waits for a browser test with a real service worker (backlog, f12-F11).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-17 00:17 ([session](../sessions/2026-10-17-0017.md)): f114-01 and f114-02 merged by the local model, each on its second attempt after a timeout; local tokens only.
- 2026-10-17 13:00 ([session](../sessions/2026-10-17-1300.md)): four fix tickets from the first checkpoint (by Copilot, standing in for Claude), f114-03 to f114-06, all merged; local tokens only.
- 2026-10-20 07:54 ([session](../sessions/2026-10-20-0754.md)): f114-07 merged on its third attempt after a lead direction ($0.78).
- 2026-10-23 07:10 ([session](../sessions/2026-10-23-0710.md)): f114-08 to f114-10, three more test fixes, all first time; a Claude checkpoint ($0.17).
- Lessons:
  - Eight fix tickets for two feature tickets, six of them on the same tests: each checkpoint judged the newest test and missed why they kept going wrong. The stand-in service workers broke `notify.js` on load, and the developer hid it with test-only hooks in the page's script. Now in `docs/agents/lead.md`: a second finding on tests that a fix ticket already rewrote is the lead's.
  - The checkpoints' findings were all real (11 of 11), but none saw the two behaviour gaps the review found: a checkpoint reads the newest diff, not what the card promised.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** finish F142 (ntfy to a closed phone) next: today these notifications only come while a dashboard page is open, and the phone freezes it after a few minutes. When it lands, the two senders should share their words, so a sign-off reads the same from both (F142's own words leave out the card's title on purpose, ADR 31 item 1). And route fix tickets on a card's tests to the lead after the first round, as the new rule says; this card's six rounds cost about 10 hours of the local model.

### 7. What clogged the factory line
- **Failed attempts:** about 5.5 hours. Three attempts timed out after 75–80 minutes each (f114-01, f114-02, f114-06), and f114-07 failed twice (97 minutes) before its direction. Unclog: split a ticket that spans `notify.js`, `sw.js` and the browser tests in `test_app.py`, or give it to the lead (the F14 rule already covers big browser tests).
- **Fix tickets:** about 10 hours of model on f114-03 to f114-10, six days apart in three batches, behind the board's order. Unclog: the new lead rule above; the review cleared the cause in one pass.
- **Stops for you, limit waits:** none on this card. The first two checkpoints ran on Copilot because Claude's allowance was held for other work; they found real problems, and cost nothing.

## What was built
- `factory_dashboard/overview.py`: `notices` words each open item from its kind and its card (D1): title, body and link with the page's project. `#live-facts` carries them as `data-notices`; `data-needs` is gone.
- `factory_dashboard/static/notify.js`: one notification per look (D2): an item alone shows itself, several make "N things need you" opening `/planning`. The notification's `data` carries its link; without a service worker, the page's own notification navigates on a tap (D3). The service worker's message is accepted only for a local path.
- `factory_dashboard/static/sw.js`: a tap focuses an open dashboard page and posts it the link, or opens the link when none is open (D3).
- Fix tickets f114-03 to f114-10: links encode the project, bundles keep it, the rejected-worker fallback navigates, and the tests check titles, bodies, links, batching and the tap.

Tests read: f114-01 and f114-02 edited existing tests in `test_overview.py` to follow `data-needs` going away (D1, D2); each edit is honest. The fix tickets' edits in `test_app.py` were read one by one and are covered by F3 below.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | `notices` drops every kind it doesn't name; the "main is red" item (f106-06) never notified, and the `all_done` branch was dead | Fixed: the Overview kinds are one table with "A check fails on main", and any other kind notifies as "Something needs you"; `test_a_kind_without_its_own_words_still_notifies` |
| F2 | should-fix | claude | All work done in the same look as a new item hid the item: the last review's sign-off came as "All work done" | Fixed: all done joins the look's items, so they make one bundle; `test_a_sign_off_in_the_same_look_as_all_done_is_not_lost` fails on the old code |
| F3 | should-fix | claude | `window._notifyCheck` and `_notifyEstablishBaseline` in production code, and a `try/except` in eight tests, hid stand-in service workers that made `notify.js` throw on load | Fixed: hooks gone, stand-ins complete, two helpers drive the page as htmx does, a duplicate test removed |
| F4 | nit | claude | The tap tests accepted any URL holding `/?` | Fixed: they wait for the decision's exact link |
| F5 | nit | claude | `proposals: Sequence[object]` read through `isinstance(p, object)` and `getattr` | Fixed: `Sequence[DeskItem]`, plain reads |
| F6 | nit | claude | The fallback notification in `.catch` was outside the `try` | Fixed: one `direct()` helper for both paths |
| F7 | nit | backlog | A failed reply is told by the runner's words ("The lead couldn't answer") | `docs/backlog.md` |

Checkpoint verdicts: all eleven checkpoint findings confirmed (C1035-3 to -6, C1044-3 to -5, C1106-1, C1337-1 to -3; the first eight are keyed to F69 and F68, whose checkpoints read F114's merges). F1, F2, F3 and F5 were missed: each was in the diffs the first checkpoint read. Score: 5/10. The feature works as the card asked, and the words and links are right, but it took eight fix tickets, two behaviour gaps reached the review, and the tests hid a broken setup behind hooks in production code.

Checked and fine, with one tightening: the page takes a service worker's link only as a path on the dashboard; the review added `/\host` to the refused `//host`, since Chrome reads both as another site (the links are the dashboard's own, so nothing could exploit it; F6's change, tested); every link keeps the project, encoded; a planning reply counts only its own card's open proposals (`/planning/<card>/proposals/`, so f1 never counts f10's). ruff and mypy pass; the dashboard and runner suites pass.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
- F7 (above), in `docs/backlog.md`.
- C1337-2 (the `sw.js` test reads source order) is already the backlog's f12-F11.

## Factory
- **Flow:** no stops for the owner, no limit waits on this card. Three checkpoints, the first two by Copilot standing in for Claude. Ten developer tickets, one direction. The card's tickets ran on 17, 20 and 23 October, in board order between other cards.
- **Models:** Qwen built everything: 2 of 10 tickets needed a second attempt after a timeout, 1 needed three attempts and a direction, the other 7 fix tickets passed first time. Claude: $3.87 planning, $0.78 direction, $0.17 checkpoint before this review. Copilot's stand-in checkpoints found six real findings.
- **What to change:** the fix-ticket chain. Each checkpoint asked for better tests and got them, but nobody asked why the tests needed a manual trigger. A finding that recurs on the same tests now goes to the lead (`docs/agents/lead.md`, Known range, F114). A gate that refuses `window._` hooks in `factory_dashboard/static/` would catch the hook itself, but it has happened once; worth a check if it recurs.

<!-- runner report -->
<!-- /runner report -->
