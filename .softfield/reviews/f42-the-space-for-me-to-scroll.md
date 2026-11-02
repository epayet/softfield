# Review: F42, the space for me to scroll

- **Status:** done, signed off by the owner on 2026-10-29.

## Sign-off sheet

### 1. What changed
On a phone, the screen goes to what you read:
- **The top bar slides away** when you scroll down a page, and comes back as soon as you scroll up even a little, or when you're back near the top. A small wobble of your thumb (under 8 px) doesn't hide it. On a computer (640 px wide and up) the bar stays where it is.
- **A mock-up review** has an "Open the mock-up" button above the mock-up. It opens the mock-up full screen in a new tab. On a phone the small frame is gone and only the button shows; on a computer the frame stays, now as tall as the window allows (at least 480 px).
- **"Your review" at the bottom of a proposal** is one short row on a phone: the count of comments, the Approve button and the closed "Reject…" fold, side by side. Its heading and its standing sentence ("Every point is agreed unless you comment on it.") are hidden there; the runner's answer still shows once you've pressed a button. Opening "Reject…" gives it a row of its own.

### 2. How to test it yourself
1. On your phone, open the Overview (or any long page) and scroll down: the top bar slides up out of sight.
2. Scroll up a little: it comes straight back. Scroll back to the top: it stays.
3. Open a card's mock-up proposal from Planning: there is an "Open the mock-up" button and no small frame. Tap it: the mock-up fills a new tab.
4. Back on the proposal, scroll to the bottom: "Your review" is one row with the count, Approve and "Reject…". Tap "Reject…": it opens on a row of its own with its button.
5. Press Approve: the dock shows "Asked…" (the runner's answer) under the row.
6. On the computer, open the same proposal: the mock-up frame is there, nearly the window's height, with the button above it, and the top bar doesn't move when you scroll.

### 3. Left for later
- f42-03 (ready, developer): the four new tests copy the same twelve-line setup; one shared helper.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-29 00:52 ([session](../sessions/2026-10-29-0052.md)): 2 developer tickets. `f42-01-review-page-room` stalled twice ("no edit after 20 min") and was finished by the lead; `f42-02-top-bar-steps-aside` stalled twice and passed on its third attempt (51 min). Lead about $2 on Opus (two directions, one escalation), Sonnet $0.16 for the checkpoint; the local model read 686k tokens.
- Lessons:
  - Layout that must be measured in a browser stalls Qwen even when the direction names the exact cause; the escalation turned the phone-row fix into a worked example in `docs/agents/developer.md`.
  - f42-02 passed but dropped one sentence of its ticket, the 8 px threshold; its test only made big scrolls, so nothing caught it. The checkpoint saw it as a nit; the review fixed it and added the small-scroll check.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** route phone-layout tickets (rows out of columns, sticky docks, anything measured with `bounding_box()`) to a lead ticket on Sonnet from the start: two out of two stalled here, and the lead finished one anyway, which is the owner's "who builds what" rule. And when a ticket gives a number (8 px, 72 px), its Done when should name a check for it, so a developer can't pass while dropping it.

### 7. What clogged the factory line
- **Stalled local attempts, 80 minutes:** four Qwen attempts each stopped after 20 minutes with no edit (two per ticket). Unclog: phone-layout work goes to a lead ticket (above), and the 20-minute stop stays, as it did its job.
- **The passing attempt, 51 minutes** for about 15 lines of JS and CSS: slow but merged.
- No limit waits, no stops for you.

## What was built
- `factory_dashboard/templates/proposal.html`: an "Open the mock-up" link (`target="_blank" rel="noopener"`) above the frame, which keeps `sandbox="allow-scripts"`; `#review-status` carries `data-has-answer`, set to true when htmx swaps an answer into it (f42-01).
- `factory_dashboard/static/dashboard.css`: the link's 44 px plate; the frame `max(480px, calc(100dvh - 220px))` tall and hidden under 640 px; the phone dock as one row (direction set, the count shrinking with `min-width: 0`, the Reject fold wrapping only when open via `:has(#reject[open])`); `header.bar.steps-aside` moves the bar up under 640 px, with a 0.2 s transition only when motion is allowed (f42-01, f42-02).
- `factory_dashboard/templates/base.html`: one passive scroll listener that hides and shows the bar on a phone (f42-02; the threshold fixed by this review).
- Tests: two in `test_proposal.py` (the link at 390 px, the frame at 1024 px), two in `test_thread.py` (the compact dock, the answer after sending), one in `test_app.py` (the bar on scroll, phone and desktop). No existing test was changed; the session report lists `test_app.py` because a test was added to it.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | The top bar hid on any 1 px scroll down past the bar's sticky `top` (0), not after 8 px past its height as the ticket asked | Fixed in `base.html`: the way down counts from the last scroll up and needs more than 8 px past `bar.offsetHeight`; `test_phone_top_bar_steps_aside_on_scroll` now checks a 5 px jitter leaves it and two small steps hide it |
| F2 | should-fix | local | The same twelve-line mock-up review setup is copied into four new tests across `test_proposal.py` and `test_thread.py` | Ticket `f42-03-one-mockup-review-fixture` |
| F3 | nit | claude | On a phone the hidden mock-up frame still loaded and ran its scripts | Fixed: the frame is `loading="lazy"`, so a `display: none` frame isn't fetched; the 1024 px sandbox test still passes |

Checkpoint verdicts: C1556-2 (no scroll threshold) **confirmed**; it is F1, which I graded should-fix because the ticket asked for the threshold. No finding counts as missed: the checkpoint read f63-02 and f42-02 only, and F2 and F3 are in f42-01, which the lead finished. Score: 7/10: every Done when met, the sandbox kept, the phone row right after the lead's finish; one sentence of a ticket dropped and a copy-pasted fixture.

Checked and fine: the out-of-band status swap replaces `#factory-status` inside the bar, not the bar, so the class survives the poll; from 640 px the `steps-aside` rule doesn't apply even if the class is left on after a rotation; the `data-has-answer` rule is scoped to `.proposal-page`; `--accent` is a token, light theme included; the dock's 72 px check reads `bounding_box()`s as `developer.md` asks.

After the review's fixes, `test_proposal.py`, `test_thread.py` and `test_app.py` pass (234 tests) and ruff passes. A full `tests/runner tests/factory_dashboard` run reached 90% with no failure before the session's time limit stopped it (the 17 errors it printed came after the stop, most likely tests cut off mid-run). The rest, run on its own afterwards, passed: `test_timeline`, `test_tickets`, `test_reports`, `test_requests`, `test_projects` (145 tests). The runner's gates run the whole suite before merging.

The French: no `coucou/locale/fr/` change in this milestone. No browser here for screenshots; the Playwright tests measure the phone and desktop layouts.

## Factory
- Flow: two developer tickets, 0/2 first time, four 20-minute stalls, one escalation (finished by the lead), two directions; no stops for the owner, no limit waits, no parks.
- Models: Qwen ~131 minutes of model for one merge; Opus about $2 (directions $1.08, escalation $0.89); Sonnet $0.16 for the checkpoint, which caught the threshold but called it a nit.
- What to change: phone-layout tickets go to a lead ticket on Sonnet (a line in `docs/task-writing.md` if the next layout card stalls Qwen again); a number in a ticket gets its own Done when check.

<!-- runner report -->
<!-- /runner report -->
