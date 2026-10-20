# Review: F49, the lead merges repeated cards itself and keeps what both said

- **Status:** done, signed off by the owner on 2026-10-20.

## Sign-off sheet

**Expected:** your note was "don't ask me to merge conversations, just do it and keep context from both in a smart way". When the lead finds that a card repeats another, it merges them right away, with no Approve button. The kept card holds both cards' notes word for word, plus the lead's short summary of the other card's thread. The kept card's next answer knows that conversation. Both threads say what happened.
**Done when:** a merge is applied in the planner's own job, in one commit by the lead. The kept card has the duplicate's notes, then "What was said on F44's thread:" and the summary. The duplicate's thread is in `.factory/planning/`. The kept thread says "Merged F44 here: …", and its next answer reads F44's thread, even on a resumed session. A merge the runner can't apply (tickets, drafts) still waits for you.

### 1. What changed
- **No Approve button for a repeat** (f49-01, 2026-10-08): the lead merges an idea or planning card that repeats another as soon as it answers. The commit on main reads "F44 merged into F41 by the lead".
- **The lead carries on on the kept card** (f49-03, done with you on 2026-10-13): your note moves to the kept card's thread, and the lead answers there. A message written on the merged-away page goes there too.
- **Context from both** (f49-02, this run): under your notes from the gone card, the kept card's doc now has "What was said on F44's thread:" with the lead's few lines (what was asked, what was answered, what is still open). Your words are never rewritten; the summary only sits beside them.
- **Nothing is lost:** the gone card's whole thread is saved in `.factory/planning/<its name>.md`, in the same commit.
- **Both threads say it:** the kept thread gets "Merged F44 here: <summary>", and the gone one points to the kept one.
- **The next answer knows:** the kept card's next lead job reads the gone card's thread once, as "From F44's thread, merged here:", even when it carries on an earlier conversation.

### 2. How to test it yourself
1. On your phone, plant two ideas that say the same thing ("the try again button does nothing" and "try again and dismiss don't work"). Chat a little on the first.
2. Send a message on the second one. Once the lead answers, the desk shows no merge to approve, and the board shows one card fewer.
3. Open the kept card's page: its thread says "Merged F… here:" with a summary, and the lead's next answer there talks about what was said on the other card.
4. Open the gone card's page: it links to the kept one.
5. On the kept card, say "that wasn't a repeat, split it back". The lead should propose a seed that plants the card again with its notes (D6).

### 3. Left for later
- Two small points, in `docs/backlog.md`. The saved copy of the gone thread misses the lead's last reply, the one that proposed the merge (your words are all there, and the database keeps the reply). A card merged twice in a row, before the lead answers, loses the "read once" of the first merge (the summary stays on the card).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-08: planned with you. f49-01 (the runner applies merges) done by the lead (`6f1db63`).
- 2026-10-13: f49-03 (the lead carries on on the kept card) done by the lead with you, after F107 (`1fefa51`).
- 2026-10-20 00:08 ([session](../sessions/2026-10-20-0008.md)): f49-02 merged on its first attempt, a lead ticket (protected runner code, test first). The other five merges in that session were F15's.
- 2026-10-20: this review, round 1. Three nits: one fixed in the review, two in the backlog. Round 2 (06:41) checked that fix and found nothing new.
- Lessons:
  - **Write the test's data in the order production writes it.** The merge test stored the lead's reply before merging, but the real job stores it after, so the test can't see the missing reply in the export (F1). Same lesson as F109 ("fixtures that don't look like real data"), smaller stakes.
  - **A protected, test-first lead ticket of difficulty 6 went through on its first attempt,** with no checkpoint findings. Splitting F49 into three tickets of one decision each paid off.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Try the merge live with the test above. Real merges are rare, so a planted pair is the quickest way to see the summary's quality. If the summaries read thin, sharpen the planner brief, not the code.
  - D6's "undo by asking" has no test, since it rests on the planner's judgement. If you ever need it, check that the seed brings back the notes and the summary. Make it a button only if it goes wrong once.

### 7. What clogged the factory line
- **A runner restart** after the lead changed `runner/` (f49-02 is runner code). Fix: none needed, by design.
- **f49-02 was ready from 2026-10-13 and ran on 2026-10-20**, after other priority-1 work (F109, F15). Nothing blocked it. Fix: none, it's the order you set.
- I couldn't read hours per wait from the metrics database here (a review job has no query command, backlog f53-review).

## What was built
- **f49-02** (`runner/planner.py`, `requests.py`, `loop.py`, `prompts.py`, `metrics.py`):
  - A `merge` proposal takes an optional `summary`. `_proposal` refuses one that isn't text, so the reply's block is unread, with the reason.
  - `merged_card` puts the duplicate's notes first, then "What was said on F44's thread:" and the summary. Lines in the summary that start with `>` or `#` are escaped, so the lead's words can't sign the card off, open a section or pass for another merge heading (tested with `merged_keys` and `card`).
  - `_merge` exports the duplicate's thread (`_export`, which now takes the key and title, with an "it was merged into F10" line), in the merge's own commit. Both undo paths (lead and owner) remove the export the merge made, since `reset --hard` leaves untracked files.
  - `_merged` adds the kept thread's "Merged F44 here: <summary or title>" line and records the duplicate in a new `planner_threads.merges_unread` column (migration 14).
  - `run_planner` adds each unread merged thread's `history` to the prompt, also on a resumed session. It marks them read only after a job that succeeded, keeping a merge that this same reply applied for the next job.
- f49-01 and f49-03 were on main before this milestone's start tag, so their reviews were the sessions they were built in (2026-10-08, 2026-10-13).

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | nit | backlog | A merge made on the duplicate's own thread exports it before `run_planner` stores the reply that proposed the merge, so the export lacks that reply. The test stores the reply first and can't see it | Backlog, with the fix: store the reply before `_auto_merge`, or pass its text to `_export` |
| F2 | nit | backlog | A kept card merged away again before its next job: its `merges_unread` are never read | Backlog: carry the list over in `_merged` |
| F3 | nit | claude | `planner.prompt`'s docstring still said `earlier` is only a sessionless job's history | Fixed |

No checkpoint findings to judge: f49-02 was a lead ticket.

Read and found sound:
- **Read once:** the unread list is cleared only for the merges the job read, after `result.ok`. A failed job keeps them, and a merge that the same reply applied stays for the next job (the kept thread's `_carry_on` job). The loop test checks the history once on the resumed session, before the carried note, and not in the job after.
- **Undo:** if a later merge fails in an approval with several merges, the exports already made are removed too (`moved` is filled as it goes). The test with a failing commit checks main and an empty `git status`.
- **Escaping:** the summary can't forge `## Notes`, `> **State:**` or a `### From F99:` heading.
- **The owner's words:** the notes still move word for word (`card_notes`). The owner's messages are stored at request time, so the export always has them.
- French: nothing to check, no `coucou/` file changed. Screenshots: nothing new on screen.

Edited existing tests: `test_a_merge_in_a_planner_reply_is_applied_at_once_by_the_lead` (the new kept-thread line added to the expected list), `test_approving_a_merge_moves_the_notes…` (the export added to the commit's files) and the migration count in `test_metrics.py`. Each edit only adds what the decisions asked for.

Checks after the fix: `uv run pytest -q tests/runner tests/factory_dashboard` gave 2,404 passed (18 min 27), and ruff is clean on the changed runner files.

Score: 8/10. Every Done-when line is met and tested, including the resumed session and the undo. The design keeps the owner's words beside the summary, as asked. Two small edge cases are left, one of them hidden by a fixture written in the wrong order.

Stop reason: none. One finding fixed, two nits in the backlog; nothing for round 2.

**Round 2** (2026-10-20 06:41): the fix diff is the docstring alone (F3), plus the backlog lines for F1 and F2 and the review itself. The docstring matches what `run_planner` does. `uv run ruff check runner/planner.py` is clean, and `tests/runner/test_planner.py` gave 213 passed. F1 and F2 stay in the backlog as routed, and no new finding came up. The loop ends here with the score unchanged at 8/10.

## Factory
- **The flow:** three lead tickets over three sessions. f49-02 merged on its first attempt, with no direction, escalation or park. There was no stop for the owner in this run (f49-03 was done with them earlier, after F107).
- **Models:** all three tickets were Claude's (protected runner code). The local model did F15's five tickets in the same session, not F49's. Numbers below.
- **What to change:** nothing new. The F109 lesson on fixtures now covers the order of writes too. A line for `docs/task-writing.md` isn't worth it until it costs more than a nit.

## Workflow observations
- The milestone's start tag came after f49-01 and f49-03, so this review read only f49-02's diff. That's right for code already on main, but the sign-off sheet has to name the earlier tickets from git history.

<!-- runner report -->
<!-- /runner report -->
