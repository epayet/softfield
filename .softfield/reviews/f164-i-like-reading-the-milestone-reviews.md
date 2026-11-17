# Review: F164, plant a review's ideas straight from the review

- **Status:** reviewed (round 1), waiting for the owner's sign-off.

## Sign-off sheet

**Expected:** every idea a review suggests shows as a plate with Plant and Plant and ask the lead, on the card's thread and on its milestone page; pressing one shows it on its way at once, and once planted the plate links to the new card.
**Done when:** F19's thread shows its idea Planted, linking to F166; F28's and F135's ideas have their two buttons and turn dashed "On its way" when pressed; a factory idea from Travel companion's review plants on Softfield's board; the next review writes each idea as a quoted line.

### 1. What changed
- **A review's ideas are plates you can plant.** Each quoted `> ` line of a sign-off sheet is a plate with **Plant** and **Plant and ask the lead**. It shows on the card's thread under "Ideas from this review · N", and in place on the milestone page, where it used to show as "&gt; …".
- **Pressing one shows it at once.** The plate turns dashed, its buttons go, and it says "On its way · planted at the runner's next pick". After the runner plants it, the plate shows the new card's number and links to its thread. If the runner refuses it, the plate says why and the buttons come back.
- **Ideas you planted by hand count too.** F19's idea already shows "F166 Planted", because you copied it into the Plant box yourself.
- **Factory ideas go to Softfield's board,** even from another project's review. Travel companion's M2 review shows its idea "for softfield".
- **Reviews now write their ideas this way.** Every suggestion that needs a card is one quoted line under Product or Factory in "What next". A small fix worth a run is a quoted line too, instead of a bug ticket set aside on the board (ADR 43).
- This review fixed two things itself. Pressing one idea could show a different idea as on its way when one idea's text started with the other's. And an idea in a later section, like What clogged, could get the area of a What next bullet.

No mock-up pictures were taken for this card ("none"), so there is nothing to compare.

### 2. How to test it yourself
1. On the phone, open F19's thread (`/planning/f19`). Under "The review", "Ideas from this review · 1" shows the Plans idea with "F166 Planted · open its thread ›" and no buttons. Tap it: F166's thread opens.
2. Open F28's thread. Its gate idea has Plant and Plant and ask the lead. Press **Plant**: the plate turns dashed orange at once and says "On its way". Reload: it still does.
3. After the runner's next pick, reload F28's thread. The plate links to the new card. Open it: its notes end "From F28's review."
4. Open the board, pick Travel companion, and open M2's milestone page. In "What clogged", the "nothing to do" idea is a plate marked "for softfield". If you plant it, the card shows up on Softfield's board, not Travel companion's.
5. Open F135's milestone page from the board. Its idea shows as a plate in place, inside "What next", not as "&gt; …".

### 3. Left for later
Nothing.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-21: the planner (Opus, 5 min) wrote the plan: four tickets, 01 and 03 for the lead, 02 for a developer.
- 2026-10-23 ([session](../sessions/2026-10-23-1549.md)): the local model built f164-02 (37 min). The checkpoints then found a new hole in its request matching three times in a row, and the local model fixed each one: f164-02b (41 min), f164-04 (16 min) and f164-05 (23 min). Each passed on its first attempt. 0 Claude tokens on the code.
- 2026-10-27 ([session](../sessions/2026-10-27-2319.md)): the lead found f164-05's test gave both ideas the same answer, so it couldn't tell a wrong match, and wrote f164-06.
- 2026-11-17 ([session](../sessions/2026-11-17-0406.md), [session](../sessions/2026-11-17-0903.md)): Claude (Sonnet) built the four lead tickets 01, 06, 03 and 07 in about 51 minutes for about $1.29, each on its first attempt.
- This review: fixed F1–F4 itself (the matching in one function, and four tests).
- Lessons:
  - **A matching function patched four times is worse than one written from the rule.** Each local fix added a loop for the case the checkpoint named. By the end there were three loops, two of them dead, and a check repeated after them, and it still matched across ideas. Here the lead rewrote it as one pass straight from D3. See the Factory idea below.
  - **Checkpoints helped, one hole at a time.** All five of their findings were real, but each one found only the next case. None of them read the code against D2 and D3 as a whole, so the section rule (F2) slipped through.
  - **A test of what a press does needs a browser.** f164-03's tests read only the server's HTML, so nothing checked the plate going dashed. One browser test now does.

### 6. What next
- **Product:** on hold, as you asked. Softfield is the project here, so its ideas are under Factory.
- **Factory:**
  - When the checkpoints keep sending one function back to the local model, the lead could take it after the second fix, as it can for an escalation. Worth a planted card:
    > Runner: when a third fix ticket would touch the same function as two fix tickets before it on one card, give it to the lead instead of the local model, so a function isn't patched case by case.
  - The plates have no "not for me" button. Ideas you don't want stay on the page with their buttons. That's fine for now, so no card yet.

### 7. What clogged the factory line
- **The lead tickets waited 25 days** (23 Oct, when the developer work merged, to 17 Nov). Claude wasn't idle: it ran about 150 lead tickets, plus plans and reviews, for cards above F164 on the board. That is the board's order working as meant, so nothing to unclog. Move a card up if you want it sooner.
- **Three extra local fix rounds** on 23 Oct, about 80 min of the local model after f164-02's 37 min. Each passed, but together they left messy code that this review rewrote. The Factory idea above is the unclog.
- **One runner restart** after f164-01 and f164-07 changed `runner/`. That is expected for protected code.
- No waits for limits, no failed attempts, no stops for you.

## What was built
- **f164-01** (`runner/prompts.py`, `runner/instructions/lead.md`): the review prompt asks for each idea that needs a card as one quoted line in the owner's plant-note voice (D1). Tested in `tests/runner/test_prompts.py`.
- **f164-02, 02b, 04, 05, 06** (`factory_dashboard/milestones.py`): `review_ideas` reads each quoted line of the stored sheet, with its id, area, target project (the factory's own, the registered repo with `runner/loop.py` and `factory_dashboard/app.py`, for factory ideas) and its state from that project's `plant` requests (D2, D3).
- **f164-03** (`_partials/idea.html`, `thread.html`, `milestones.py`, `thread.py`, `dashboard.css`): the plate. The thread lists the ideas after the review's sections. The milestone page draws each quoted line in place as the next plate. The buttons post the Plant box's own `plant` request with `from`, to the idea's project, and swap to "On its way" before the request is sent (D4, D5). Nothing changed in `factory_dashboard/requests.py`. Its `project` form field already let a plant go to another project.
- **f164-07** (`runner/prompts.py`, `lead.md`, `docs/workflow.md`, `docs/how-it-works.md`): a `later` finding is a quoted line under What next, not a set-aside bug ticket (D7, ADR 43). A security finding never takes that route.
- Checked live: F19's thread shows "Ideas from this review · 1" with F166 Planted, and Travel companion's M2 page shows its idea for softfield.
- One small difference from D4: the request's text adds " From F28's review." after a space, not on a new paragraph. The planted notes still end with it, so it was left.
- No French in this milestone: it is all factory.

## Findings and resolutions
- **F1, should-fix, fixed by the lead:** pressing one idea counted for another idea its text started with ("Add X to Y" made "Add X" show on its way). The matching also held two dead loops and a second check after them. It is now one pass per project, newest first: a request whose `from` is the idea's id, else one with no `from` whose text matches (D3, so F166's hand-made plant still counts). Test: `test_a_press_of_another_idea_never_counts_for_one_its_text_starts_with`.
- **F2, nit, fixed by the lead:** an idea's area came from the last bullet of any earlier section, and a sheet without What next gave no ideas at all. D2 says "in its section" and "any section". Two tests.
- **F3, nit, fixed with F1:** the function looked up every project's folder for each factory idea, and read every request again for each idea. It now does each once.
- **F4, should-fix, fixed by the lead:** nothing tested the press itself. A browser test now presses Plant, sees the dashed plate with no button left, and checks the stored request.
- **F5, nit, report only:** a quote wrapped over several lines is read only up to its first line, and a quote with `>` on every line becomes several ideas. `lead.md` asks for one line and every review so far writes one, so nothing changes. The first test's fixture uses a wrapped quote, which makes it look as if wrapping worked.
- **Checkpoint findings:** all five confirmed. C1362-1 and C1362-2 (no other project found, one request per project) were fixed by f164-02b. C1366-1 (ideas not matched one by one) by f164-04. C1369-1 (a request with no `from` matched to the wrong idea) by f164-05. C1485-1 (a test that couldn't tell the ideas apart) by f164-06. F2 was in f164-02's diff, which the first checkpoint read: marked missed.
- Score: 7/10. Every Done-when line is met and the plates work, but it took four local rounds and a rewrite to get the matching right.

## Backlog
Nothing added.

## Factory
- **Flow:** 8 tickets, all merged on their first attempt. The local model built the developer ticket and three fix tickets on one day. Claude built the lead tickets 25 days later, in board order. No stops, no escalations, and you didn't need to step in.
- **Models:** the local model (qwen3.6-35b-a3b) did about 2 h of work across the four developer tickets, for $0 in API costs. Claude (Sonnet) spent about $1.29 on the four lead tickets, and Opus $2.33 on the plan. Checkpoints were cheap ($0.22 for Claude's), but each found one case only.
- **To change:** see the Factory idea in "What next": hand a function to the lead after its second fix round.

<!-- runner report -->
<!-- /runner report -->
