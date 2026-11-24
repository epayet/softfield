# Review: F97, Needs you steps aside: Now first, a box of desk counts at the bottom

- **Status:** done, signed off by the owner on 2026-11-24.

## Sign-off sheet

### 1. What changed
- The Overview opens on Now, on a phone too. Needs you is now a calm box at the very bottom, after While you were away.
- Each project's desk is one small plate: its count, its name, "desk ›" to its Planning room; no titles. The other items (Claude's reserve, an ADR, a stopped review) sit under the plates as before.
- A stopped runner, tickets waiting on an idle runner, or a check failing on main now show as a red "Line stopped" strip at the top of Now, not in Needs you.

### 2. How to test it yourself
1. Open the Overview on your phone: Now is the first panel.
2. Scroll to the bottom: Needs you shows "1 wardrobe-teller desk ›", "2 travel-companion desk ›", "6 softfield desk ›", then travel-companion's two reserve questions (today's real values).
3. Tap a desk plate: it opens that project's Planning room. The Planning tab still says the same count as softfield's plate.
4. Next time the runner stops or main goes red, check the red "Line stopped" strip at the top of Now, and that your phone still gets the notice.

### 3. Done when, as of now
- **Met:** f97-01 merged (finished by the lead after three developer attempts).
- **Met:** Now is the first panel and Needs you the last, with one plate per desk, each opening its Planning room, then the reserve questions; the Planning tab keeps its count (live page read on 2026-11-24).
- **Not yet:** nothing stops the line today, so the "Line stopped" strip and its phone notice are proven by the tests only (stale heartbeat, idle queue, a failing check on main).
- **Your check:** the phone view, and that notifications come as before.

### 5. Decisions made along the way
- **The strip still shows the need's command (`softfield run`).** The ticket asked for the strip to draw each item as Needs you draws it. Replacing those commands with a button is a separate change to the runner's and queue's items. *f97-01, lead.*
- **The plate omits the project name on a one-project factory.** It shows just "N desk ›", because the project plate only appears when the factory has several projects (F132 D3). *f97-01, lead.*

### 6. What next
- **Product:** product work is on hold, so nothing to suggest here.
- **Factory:**
  > The "Line stopped" strip and Needs you still show terminal commands like `softfield run` (built in `needs_you()` in `factory_dashboard/overview.py`): replace them with plain words or a button the owner can press from the dashboard.

### 8. How the work went
- The local model's last attempt overwrote `test_overview.py` (5,700 lines down to 395) and spent the attempt retyping it, so the max-diff gate failed. The lead added note 6 to `.softfield/developer.md`: add tests with Edit at a file's end, never Write over it.
- The new main-red test used a tidier item than the runner writes: no command, the check as subject, a long text with an apostrophe. The review aligned it with `red_main_text`.

### 9. What clogged the factory line
- Three days passed between the second developer attempt (20 Nov 23:38) and the direction job (23 Nov 22:35), while the ticket waited on the queue.

<!-- runner report -->
<!-- /runner report -->
