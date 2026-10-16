# Review: F12 notifications, asked once

- **Status:** done, signed off by the owner on 2026-10-16.

## Sign-off sheet

1. **What changed**
   - The "Turn on notifications" button is gone from the top bar, and with it the phone layout that put it on the left.
   - On the address you use (`http://<this machine>:8765`), a bar under the top bar now says the address can't show notifications yet and gives the three Chrome steps, with your own address filled in and a Copy for each thing to paste. "Got it" hides it.
   - Once Chrome trusts the address, the bar asks instead: "Get a notification when something needs you, or when all the work is done?" with Yes and No thanks. Yes opens Chrome's own prompt. Either answer hides the bar for good in that browser.
   - A small service worker shows the notifications, which is what Chrome on Android needs. A tap on one brings an open dashboard tab forward, or opens the dashboard.
   - **As merged, none of this showed on your address.** Chrome answers "denied", not "not asked yet", on an address it doesn't trust, and the bar only showed on "not asked yet". So on the LAN address there was no bar at all. The review fixed it and three things beside it (findings F1 to F5 below).
2. **How to test it yourself** (restart `uv run runner dashboard --lan` first, so the pages load the new script)
   1. On the desktop, open the dashboard at its LAN address. The bar gives three steps and only one button, "Got it".
   2. Do the steps: paste `chrome://flags/#unsafely-treat-insecure-origin-as-secure` in a new tab, write the dashboard's address in the box, set Enabled, Relaunch. Tap "Got it" before or after: it makes no difference.
   3. Back on the dashboard, the bar now asks the question. Tap Yes, then Allow in Chrome's prompt. The bar is gone and stays gone after a reload.
   4. Leave a page open until something new needs you (the next item under "Needs you"), or until all the work is done. Within a few seconds a notification appears. Click it: the dashboard tab comes forward and the notification closes.
   5. Repeat 1 to 4 on the phone. The Copy links work on the phone but don't yet say so (f12-04).
   6. If no bar shows at step 1 or 3: this browser answered before. In Chrome, the icon left of the address → Site settings → Delete data, then reload.
3. **Left for later**
   - Three tickets queued by this review:
     - `f12-03-remove-review-probe` (lead): removes a scratch test file I left and couldn't delete (see finding F8). It goes first; the other two wait for it.
     - `f12-04-copy-says-copied` (developer): each Copy becomes a real button and reads "Copied" after a tap.
     - `f12-05-service-worker-path-test` (developer, tests only): a test that notifications go through the service worker when there is one.
   - Notifications with every dashboard page closed: the roadmap (ntfy, [ADR 26](../adr/26-notifications-on-the-home-wifi.md), Consequences).
   - Three nits in `docs/backlog.md` (F9 to F11).
4. **Decisions waiting for you:** none. One I took that you may want to know: "Got it" on the steps no longer counts as an answer to the question. As planned it did, so after you trusted the address the dashboard would never have asked. ADR 26 item 2 says the steps show once, which still holds.
5. **How the work went**
   - [2026-10-10 03:02](../sessions/2026-10-10-0302.md): `f12-01-notifications-asked-once` and `f12-02-notify-bar-tests-and-sw-focus` both merged at the first attempt by Qwen (59 and 36 min, 3.5M local tokens together). One checkpoint between them found two real problems and wrote f12-02. No direction, no escalation.
   - Lessons:
     - The feature passed every gate and the checkpoint, and could not work on the one address it was built for. The developer's test set up a browser state that doesn't exist (not secure, permission "default"). The review opened a real plain-http address in the test browser and saw "denied" in three seconds. lead.md's Known range now says: when a ticket depends on what the browser itself answers, ask for one test with the real API at a real address.
     - The ticket itself carried the same wrong belief ("shows only when the permission is still default") and the "Got it" dead end. Both were mine, at plan time. A fact about a browser in a ticket's Context needs the same check against something that ran as a count does.
     - I left a scratch file in the tests that a headless job can't delete, and it fails the `layout` gate until f12-03 runs. A probe now goes inside an existing test file (lead.md).
6. **What next**
   - **Product:** on hold, as you asked (2026-10-04).
   - **Factory:**
     - Do the hand check on the phone before anything else builds on notifications: nothing here has run on a real Android Chrome, and the service worker path has no browser test of its own yet (f12-05 tests the page's side with a stand-in).
     - If the phone's "only while a page is open" turns out too little, the ntfy card is the next step, and it needs none of this milestone's Chrome setting.
     - A gate idea, not yet an ADR item: a test in `tests/factory_dashboard/` that replaces `isSecureContext` or `Notification.permission` could be flagged by `test-patterns` unless another test in the same file uses the real one. I'd wait for a second case before proposing it.
7. **What clogged the factory line**
   - Nothing during the build: two first attempts, no failure, no wait for a limit, no stop for you.
   - Before it: the card was planted on 2026-10-07, ADR 26 was accepted on 2026-10-08, and the tickets merged in the night of 2026-10-10, behind F9's line tickets. In that same run f9-25 took three attempts that made no edit and an escalation; F12's two tickets waited behind it.
   - After it: this review's own mistake (F8) holds the two developer fix tickets behind a one-line lead ticket. If Claude is at a limit when it comes up, they wait for the reset. Running `rm tests/factory_dashboard/test_probe_tmp.py` yourself and committing unblocks them at once.
   - (Times are from the commits and the tickets' footers; I couldn't read the metrics database from this job.)

<!-- runner report -->
<!-- /runner report -->

## What was built

- `factory_dashboard/static/notify.js`: `setupBar` shows the bar (the question on a secure address, the steps otherwise), `registerSw` registers the service worker, and `show` goes through it when there is one, with `new Notification` as the fallback. What notifies and when (`compare`) is unchanged.
- `factory_dashboard/static/sw.js`: new; on a tap it focuses an open dashboard page or opens `/`. No fetch handler, no cache, no push.
- `factory_dashboard/templates/base.html`: the bar's markup on every page, hidden; the `#notify-me` button removed.
- `factory_dashboard/static/dashboard.css`: the bar's rules, with a phone layout; the old button's rule removed.
- `tests/factory_dashboard/test_app.py`: the two existing notification tests moved from the button to the bar (read: nothing weakened; the per-page test now asserts the bar is there and the button isn't, and that `sw.js` is served), and seven new bar tests, plus three from this review.

## Findings and resolutions

| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | blocking | claude | On a plain-http address the steps never showed: `setupBar` returned unless the permission was "default", and Chrome answers "denied" there. The test hid it by faking both `isSecureContext` and a "default" permission. | The secure-context check now comes first. The test opens `http://192.168.1.20:8765` with Chrome's own `Notification` and asserts what Chrome answers. Resolved. |
| F2 | blocking | claude | "Got it" stored `notify:asked`, the same key as Yes and No thanks, so once the address was trusted the question was never asked. The ticket asked for this; the plan was wrong. | "Got it" stores `notify:steps`. New test: with it set, the question still shows on a secure address. Resolved. |
| F3 | should-fix | claude | The steps bar also showed Yes and No thanks, which did nothing there. | Hidden on the steps bar; the test asserts "Got it" is the only button. Resolved. |
| F4 | should-fix | claude | Yes, then Chrome's prompt closed without an answer, stored `notify:asked`: the bar never came back, and with the button gone nothing else could turn notifications on. | Stored only when the prompt was answered. New test with a prompt that stays "default". Resolved. |
| F5 | should-fix | claude | `sw.js` didn't close the tapped notification (Android keeps it) and didn't wait for the focus. | Two lines. The text test of `sw.js` asserts the close. Resolved. |
| F6 | should-fix | local | Each Copy is a link with no `href` (the keyboard can't reach it) and shows nothing after a tap. | `f12-04-copy-says-copied`. |
| F7 | should-fix | local | No test runs `registration.showNotification`, the only path Android shows: in every test the registration fails and `new Notification` is used. | `f12-05-service-worker-path-test` (tests only). |
| F8 | should-fix | local (a lead ticket) | The review's own scratch file `tests/factory_dashboard/test_probe_tmp.py` fails the `layout` gate; a headless job can't delete it. It now holds no test, only a note. | `f12-03-remove-review-probe`, with `commands: [rm …]`; the two developer tickets depend on it. |
| F9 | nit | backlog | `role="body"` and `role="actions"` aren't ARIA roles. | Backlog. |
| F10 | nit | backlog | Six bar tests repeat the same `route` function. | Backlog; the review's tests use a helper, `_open_at`. |
| F11 | nit | backlog | The service worker's tap test reads `sw.js` as text. | Backlog. |
| F12 | nit | claude | A whitespace-only line left in `base.html` where the button was. | Removed. Resolved. |

(Ids are prefixed `f12-turn-on-notifications-little-feedback-button-` in the review file.)

The checkpoint's findings:
- **C747-1** (granted and denied tests pass trivially; non-secure bar untested): **confirmed**. f12-02 fixed the first half; its non-secure test was the fake that hid F1.
- **C747-2** (a tap never finds an open tab): **confirmed**, fixed by f12-02 (`includeUncontrolled`).
- **Missed:** F1 and F3 were in f12-01's diff, which the checkpoint read.

Checked and fine:
- The bar's HTML is built with `innerHTML` from fixed text and `location.origin`, which can't carry markup.
- On plain http `navigator.clipboard` doesn't exist; the Copy handler's `try` catches that and falls back to selecting the text. `navigator.serviceWorker` doesn't exist there either, and `registerSw` returns early.
- The worker's scope is `/static/`, which is enough to show notifications; `includeUncontrolled` is what lets a tap find the pages.
- The dashboard is English only: no French in this milestone.
- `uv run runner check-all`: ruff, format, mypy and translations pass; 2457 tests passed, 1 skipped. It fails on `layout` for the scratch file (F8), and failed on one ticket check that I then fixed (`tests/runner/test_tasks.py`: 120 passed afterwards). The 12 notification tests pass.
- Not checked: nothing ran on a real phone, and I took no screenshot. Whether Chrome reports "default" once the flag trusts the address is what step 3 of the hand check shows.

**Score: 5 of 10.** Two clean first-attempt tickets and a checkpoint that earned its keep, for a feature that didn't work where it was needed until the review.

## Backlog

Three nits added to `docs/backlog.md` (F9, F10, F11).

## Workflow observations (Factory)

- **Flow:** two developer tickets, two first attempts, one checkpoint, no stop, no park, no intervention. Qwen at difficulty 3–4 on one script with a worked example is inside the known range.
- **The checkpoint:** two findings, both real, both fixed by the ticket it wrote, for a Sonnet job. It read the non-secure branch closely enough to see it was untested, and not closely enough to see the dead buttons on it (F3) or that it couldn't be reached (F1). F1 needs a fact about Chrome that the diff doesn't hold; F3 was plain in the diff.
- **The plan:** the ticket's Context stated the browser's behaviour from memory, and the developer built exactly that. This is the same lesson as f1-34's wrong count: a fact in a ticket is checked against something that ran.
- **The review's cost to the line:** one lead ticket to delete a file. The review's Bash tools can't delete, which is right; the mistake was creating a file rather than adding the probe to `test_app.py`.
- **Developer tests:** f12-02 did what its Done when said (the granted and denied tests now wait for the page's script). Its non-secure test asserted `"1." in body`, which the address `http://127.0.0.1:8765` satisfies by itself; the review's version asserts each step's words.
