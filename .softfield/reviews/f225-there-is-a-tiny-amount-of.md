# Review: F225, the night switch slides by itself when a page loads

- **Status:** done, signed off by the owner on 2026-11-12.

## Sign-off sheet

### 1. What changed
The night/light switch at the top of every dashboard page no longer slides when a page opens. Its orange knob is already on the right side when the page appears, in both themes. It still slides when you press it, or when your phone changes theme on its own and you haven't picked one.

There were no pictures or mock-up for this card (the switch looks the same as before), so there is nothing to compare.

### 2. How to test it yourself
1. On the phone, open the dashboard in the night theme and move between a few pages (Overview, Board, Planning). The knob should stay at the top, lit moon, with no slide as each page opens.
2. Press the switch. The knob should slide down to the sun, and the page should turn light.
3. Move between pages again in the light theme. The knob should stay at the bottom with no slide.
4. Do the same on the computer.

### 3. Left for later
Nothing set aside. There are two small notes and neither is worth a run (see Findings).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-06: the local model (Qwen) made two attempts. The first got the CSS right and wrote the four tests, then ran out of time on one test that read the knob's place partway through its slide. The second made no edit and was stopped after 20 minutes.
- 2026-11-10: Claude wrote a direction for the last attempt. The local model went round on the same test for 30 minutes. Claude took over on the branch and finished it in 14 minutes. The local model wrote nearly all of the code.
- Lessons:
  - In a browser test, read where something sits from the page itself, not by working it out from the CSS.
  - Read a slide's end position after `transitionend`, never after a fixed wait.
  - What changed: note 8 in `.softfield/developer.md` now says this.
- Logs: `.softfield/var/runs/20261106-011143/f225-01-switch-follows-the-theme/`, `.softfield/var/runs/20261110-022911/`.

### 6. What next
- **Product:** product work is still on hold, as you asked.
- **Factory:** this ticket lost about 2 hours of local time over one wrong number. The model expected the knob at 19 px, but it sits at 17. It never printed the real value to check. Suggestion: when a browser test's number assertion fails, the developer's instructions should say to print the measured value before changing any code. Note 8 now covers this case. If it happens again on another ticket, it should become a general rule.

### 7. What clogged the factory line
Taken from the `jobs` table:
- **Local attempts that didn't merge: about 2 h 10 min.** Attempt 1 took 1 h 20 min and timed out. Attempt 2 took 20 min and was stopped with no edit. The last attempt took 30 min and failed on the same test. The fix for this is note 8 in `developer.md`, added with this ticket.
- **Waiting between attempts: about 3½ days** (11-06 17:31 to 11-10 06:11). The ticket was waiting in the queue for the last-attempt step, not being worked on. Other work took that time, so nothing sat idle because of it.
- **Claude's time:** direction 1 min ($0.38) and escalation 14 min ($0.71).

<!-- runner report -->
<!-- /runner report -->

## What was built
`f225-01-switch-follows-the-theme` (commit 91081f3b3):
- **CSS:** `factory_dashboard/static/dashboard.css` now places the knob and lights the icons from `:root[data-theme=…]`. That attribute is set in `<head>` before the first paint. Before, the CSS read the switch's `aria-checked`, which is only set at `DOMContentLoaded`. The phone rule (`calc(100% - 19px)`) is rekeyed the same way. The `transition` rule is unchanged, and `base.html` still sets `aria-checked` and the title for screen readers.
- **Tests:** four new browser tests in `tests/factory_dashboard/test_app.py`:
  - Night and light at desktop and phone size, with `aria-checked` set by hand to disagree with the theme. These test the cause, as the ticket asked, and fail on the old CSS.
  - No `transitionrun` on load in the night theme.
  - Pressing the switch starts a slide, and the knob ends at the plate's inner height minus 17 px. The test reads this after `transitionend`.

I read the code against the card's decisions D1–D3, and all three hold. The 19 theme tests pass. No existing test was changed. There is no French in this milestone.

## Findings
| Id | Grade | Route | What |
|---|---|---|---|
| F1 | nit | report | `dashboard.css:149`: the moon lights only for `data-theme="dark"`, while the ticket said anything not light is night, as the knob's rule does. The page's own code only ever sets `light` or `dark`, so only a hand-edited stored value would show it. The fix, if it ever matters, is `:root:not([data-theme="light"]) .theme-switch .moon`. |
| F2 | nit | report | The four new tests each copy the same `route()` helper. About 40 copies already exist in `test_app.py`, so the new tests just follow the file's habit. A shared helper would mean refactoring untouched tests across 4,000 lines, which isn't worth a run on its own. |

**No checkpoint findings.** No checkpoint ran on this ticket because Claude finished it.

**Score: 8/10.** The fix is right, small, and keyed on the cause. The tests test the cause, which is what the ticket warned about. It cost two local hours and an escalation over one misread number.

## Set aside
Nothing.

## Workflow observations
- **The ticket was good.** It named the trap in the test (a test that only watches a page load can pass on the old code) and asked for the test that checks the cause. Both the local model and Claude followed it.
- **What failed was debugging, not design.** The local model got the change right on its first attempt. Then it spent three attempts suspecting correct CSS, and never printed the one value that would have explained the failure. Note 8 records the fix. It would be worth watching whether similar "number off by a little" failures happen on other tickets.
- Attempt 1 ran its context to 126k of 130k, and the last attempt ran to 130,285. Long debugging sessions are filling the local model's whole context window.
