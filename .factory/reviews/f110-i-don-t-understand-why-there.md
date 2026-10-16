# Review: F110, ripe on the board means a Sign off button

- **Status:** done, signed off by the owner on 2026-10-16.

## Sign-off sheet

**Expected:** a card the board calls ripe always has a Sign off button on its page and sits on the desk under "Finished, to talk through"; a ripe card says where to sign off in plain words, not as a terminal command.
**Done when:** a milestone whose tickets are all done except ones set aside or removed, with its review written, is ripe on the board, on the line's field and on the desk, and its page has the Sign off button; a ripe card reads "Read the review and sign off" and opens the card's page at the button.

### 1. What changed
- **One rule for "ripe".** A ticket set aside or removed no longer stops a milestone from ripening on its page and on your desk, as it already didn't on the board. F31 (five tickets done, one set aside) is the case you hit: it is now ripe everywhere, with its Sign off button.
- **Ripe cards on the board say "Read the review and sign off ›"** instead of `softfield signoff …`, and a tap opens the card's page straight at the Sign off button.
- **Sprouting means a live conversation.** An idea whose conversation is archived is a seed again (F11, F15, F18, F105 were sprouting with archived threads). A sprouting card says who it waits for: "waits for your answer since 9 Oct" or "the lead is answering".
- *(Fixed in this review)* When you answer on a thread, the card says "the lead is answering" at once, not at the runner's next pick; writing on an archived idea's thread makes it sprout again straight away.

### 2. How to test it yourself
Restart the dashboard first: this review changed its code.
1. On your phone, open the Board. Every card under Ripe reads "Read the review and sign off ›", with no command on it.
2. Tap each ripe card: the page opens at the Sign off button. F31, When I click on Approve plan, is the one to try.
3. Open your desk (Planning): the same milestones are under "Finished, to talk through".
4. On the Board, check no card under Sprouting has an archived conversation, and each says who it waits for.
5. Answer a sprouting card's thread: back on the Board, it says "the lead is answering" straight away.

### 3. Left for later
- A milestone whose only tickets are all set aside shows as "Planted: tickets ready" on the board though none is ready (backlog: call it a seed).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-15 16:36, runner: f110-01 stopped twice on "no edit after 10 min", then merged after the lead's direction (local model, 69 min) ([session](../sessions/2026-10-15-1636.md)).
- 2026-10-16 00:12, runner: f110-02 and f110-03 merged first time by the local model (58 and 75 min) ([session](../sessions/2026-10-16-0012.md)).
- 2026-10-16, review round 1 (Opus): one should-fix fixed directly, one test tightened, one nit to the backlog.
- Lessons:
  - **A ticket on what the board shows must say which waiting state counts.** f110-03 read the conversation's stored messages only; the owner's reply sits as a request until the runner's next pick, so the card was wrong for up to an hour after every answer. "Show what the owner asked for at once" now has two pages following it (the thread and the board); the next ticket that reads a thread should name `owner_requests` in its Read section.
  - Three small dashboard tickets, 2 of 3 first time; the third lost 20 minutes to the edit-stop that f93-01 is about.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - One helper for "what is on its way to the runner" (pending plants, messages, sign-offs), read by every page, so each new page doesn't re-find the requests table on its own.
  - Run f93-01 (the "no edit after 10 min" stop) soon: it cost f110-01 two attempts and f95's review noted the same.

### 7. What clogged the factory line
- **f110-01 lost about 20 minutes to two "no edit after 10 min" stops** before the lead's direction got it through. What unclogs it: f93-01, already at priority 0.
- **f110-02 and f110-03 ran one after the other for about 2 h 45 min** in one session (they both change the board's card, so they couldn't run in parallel). What unclogs it: nothing to change; the order was right.

## What was built
- **f110-01** (`_field` in `factory_dashboard/line.py`): set-aside and removed tickets count for no stage on the line's field, as `_OFF` already did on the board; the desk's ripe group and the page's button read the field. Tests: `test_line.py` (set aside, removed, only set aside) and `test_milestones.py` (the button shows with a set-aside ticket). The existing field test's f9 total moved 4 → 3: f9 has a set-aside ticket (`f9-04-later`), so that edit is right.
- **f110-02** (`templates/board.html`, `dashboard.css`): the ripe card's words and its `#review` link; `#review` is the section around the Sign off button in `milestone.html`. The existing growing-card test changed from the command to the words, rightly.
- **f110-03** (`factory_dashboard/board.py`): only unarchived threads make a card sprout; `_card_note` says who the latest message waits for.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | The sprouting note ignored the owner's message still on its way (an open `plan_message` request), so a card kept saying "waits for your answer" for up to an hour after the owner answered, and an archived idea they wrote on stayed a seed | Fixed in `board.py`: an open message request counts as the owner's word at once; `test_the_owners_message_on_its_way_shows_at_once` |
| F2 | nit | backlog | A milestone with only set-aside tickets is "Planted: tickets ready" on the board and absent from the line's field (C950-1 led there) | `docs/backlog.md` |
| C965-2 | nit | claude | The "words fit inside the card" test only checked the text, and passed with no ripe card | Confirmed and tightened: it needs a ripe card and compares the boxes |
| C950-1 | nit | backlog | The set-aside-only test asserts absence only | Confirmed; part of F2 |

Tests read: every test the three tickets added, and the two existing ones they edited (both legitimate, above). Missing edge case found: the owner's message on its way (F1).

Checkpoint: both nits confirmed. F1 was in f110-03, which merged after the checkpoint had run, so it isn't a miss.

French: nothing to check, the dashboard is English only. Screenshots: no browser in this job; the tightened layout test checks the ripe card's words at phone and display sizes.

Checks after the fixes: `tests/factory_dashboard/test_board.py` 44 passed; ruff and mypy clean on `board.py`; the full `tests/runner tests/factory_dashboard` run gave 2302 passed in 16 min 43 s (started in the background, since it runs longer than one foreground command may).

Score: 8/10. Three small, correct changes that do what the card asked; one missed case of an owner preference.

## Factory
- **Flow:** three tickets, all merged by the local model (qwen3.6-35b-a3b), two first time; f110-01 needed a direction (Opus) after two edit-stops. One checkpoint (Sonnet) on f110-02, none yet on f110-03 before this review. No escalation, no stop for the owner.
- **What to change:** the "on its way" helper and f93-01, in "What next". Neither needs an ADR.

## Workflow observations
- The start tag also holds f95-01 and f106-02 (other cards' tickets) and a runner fix; this review read F110's three tickets' commits.

<!-- runner report -->
<!-- /runner report -->
