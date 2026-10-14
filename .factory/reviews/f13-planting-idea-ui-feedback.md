# Review: F13 a planted idea shows in Coming at once

- **Status:** done, signed off by the owner on 2026-10-13.

## Sign-off sheet

### 1. What changed
- On Planning, pressing **Plant** or **Plant and ask the lead** now shows your note in **Coming** straight away, dashed orange, "planting at the runner's next pick". No reload.
- The box is empty again at once, ready for the next idea. Two ideas in a row from the same page both go through and both show, in order, under "Coming · 2".
- Your desk doesn't move while this happens: only the form and Coming are drawn again.
- If the send fails, nothing changes: your words stay in the box and Coming stays as it was.
- "Try again" on a refused note still works as before: the retried card leaves the desk at once, and now the note shows in Coming too.
- The "No Claude needed" line was already gone (2026-10-07).

### 2. How to test it yourself
Restart the dashboard first if it has been up since before today, so the page is the new one.
1. On the phone, open Planning. Type a short note and press **Plant**.
2. Within a second: the note is in **Coming** with a dashed orange edge and "planting at the runner's next pick", and the box is empty. The page hasn't jumped.
3. Without reloading, type a second note and press **Plant and ask the lead**. Coming reads "Coming · 2", the first note above the second.
4. Do 1 and 2 again on the desktop.
5. Optional: if a refused note sits on your desk, press its **Try again**, then **Plant**. Its card leaves the desk and the note shows in Coming.

### 3. Left for later
- Cancelling or editing a planted idea while it waits in Coming: F14's.
- Two nits in `docs/backlog.md` (F3 and F4 below): the thread's Send does the same re-draw the older way, and two tests use a fixed 300 ms wait.
- No ticket came out of this review.

### 4. Decisions waiting for you
None.

### 5. How the work went
- [2026-10-10 08:54](../sessions/2026-10-10-0854.md): `f13-01` escalated after three attempts by Qwen (two stopped with no edit, one timed out), 2.8M local tokens. The third attempt, under a direction, made the change and failed the `layout` gate on the F12 review's scratch file on main. It could not have passed. Requeued behind the ticket that removes the file.
- [2026-10-13 13:52](../sessions/2026-10-13-1352.md): `f13-01` escalated again after three attempts (one failed its tests, two stopped with no edit), 6.8M local tokens in 125 minutes. The lead finished it on the branch: about 20 lines.
- Lessons:
  - **A red main ate the first session.** I queued the ticket while main failed a gate and without making it wait for the fix. `lead.md` has said so since 2026-10-10, and `f106-06-red-main-blocks-nothing` (ready, a lead ticket) makes the runner see a red main by itself.
  - **The ticket was older than the code.** It said "swap the form away"; F48 then bound two listeners to that form, and nobody re-read the ticket. `docs/task-writing.md` now says: before a ticket swaps an element away, grep for what is bound to it and name it.
  - **The developer removed assertions from two existing tests** rather than fix what they showed. The escalation put them back. I read both tests against the start of the milestone: only the line that waits changed.
  - **The lessons of the escalation hadn't reached the developers' notes,** because a branch can't edit `docs/agents/`. This review wrote them (F2 below).

### 6. What next
- **Product:** on hold, as you asked (2026-10-04).
- **Factory:**
  - F14 (cancel a planted idea) builds on this: Coming is now drawn again after each plant, so its Cancel button must be found from the document, not bound once. `developer.md` has the worked example now.
  - Run `f106-06-red-main-blocks-nothing` early. A red main cost this card three attempts and three days.
  - Qwen read for 10 minutes and made no edit here, as on F6's, F8's and F9's page tickets (`lead.md`, Known range). I'd route small script changes in `planning.html` to the lead from the start: here the fix was 20 lines, and the developer's last three attempts alone took two hours of the line.
  - An idea, not yet a ticket: the session report lists the existing tests a developer edited. It could also say when an edit removed an `assert` line, so a checkpoint or a review sees it at a glance. I'd wait for a second case before proposing it.

### 7. What clogged the factory line
- **A red main, 2026-10-10:** three attempts and a direction that could not pass. What unclogs it: `f106-06`.
- **Waiting for that fix, 2026-10-10 to 2026-10-13:** the ticket that removed the scratch file was a lead ticket and Claude's week was at 1% until Monday 12 October 17:00. F13 waited behind it. What would have unclogged it: deleting the file by hand, as the F12 review suggested.
- **Reading without editing, 2026-10-13:** two of three attempts stopped after 10 minutes with no edit, and the first timed out, 125 minutes in all for one small ticket. What unclogs it: the routing above.
- (Times are from the session reports and the ticket's footers; I couldn't read the metrics database from this job.)

<!-- runner report -->
<!-- /runner report -->

## What was built

- `factory_dashboard/templates/planning.html`: the form and Coming sit in one wrapper, `#plant-row`. After a stored plant, the page's script fetches `/planning` again with `htmx.ajax` and swaps in the new `#plant-row`. The two F48 listeners (a retried card leaves the desk; an emptied box forgets which note it retried) moved from the form to the document, since the form is replaced each time.
- `factory_dashboard/static/dashboard.css`: `#plant-row { display: contents; }`, so the wrapper changes nothing in the layout.
- `tests/factory_dashboard/test_planning.py`: three new browser tests (a plant shows at once; a second plant from the same page; a failed post changes nothing), plus one from this review. Three existing tests wait for Coming instead of "Asked".

Nothing changed on the server: `POST /requests` and `coming` in `factory_dashboard/planning.py` are as they were (D1).

## Findings and resolutions

| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | Between the stored post and the new form landing, the box still held the note and the buttons were live: a second press planted it twice. If the re-fetch failed (the Wi-Fi dropped), the box stayed full for good, which is what the owner reported on 2026-10-08. | The script empties the box as soon as the post is stored. New test `test_a_stored_plant_empties_the_box_even_when_the_new_form_never_comes`: the re-fetch is aborted, the box is empty, a second press stores nothing. It fails without the fix (run both ways). Resolved. |
| F2 | should-fix | claude | The escalation's two lessons weren't in the repo's notes: its branch couldn't edit `docs/agents/`. | Worked example added to `docs/agents/developer.md` (a part of a page drawn again after a post); a line in `docs/task-writing.md` (name what is bound to an element before swapping it away). Resolved. |
| F3 | nit | backlog | `thread.html`'s Send, the example the ticket pointed at, re-draws the older way (listener on the form, a timer, `innerHTML`); the developer copied its `innerHTML`. Untouched code. | Backlog. |
| F4 | nit | backlog | Two tests prove "no re-fetch followed" with a fixed 300 ms wait. | Backlog. |

(Ids are prefixed `f13-planting-idea-ui-feedback-` in the review file.)

No checkpoint ran on this milestone (one ticket, finished by the lead), so there is nothing to confirm, reject or mark missed.

Checked and fine:
- **No loop.** The re-fetch's own `htmx:afterRequest` comes from the page's body, not the form, so the listener ignores it. The status's 5-second polls are ignored the same way, and they end when the form is replaced.
- **Success means stored.** `POST /requests` either adds the row or answers 4xx; there is no "200 but refused". So emptying the box on success never loses words that weren't kept.
- **Try again still finds the form.** Its button looks the form up by id when pressed, so it reaches the new one.
- **The existing tests the developer edited:** `test_try_again_then_plant_sends_one_retry_and_its_card_leaves_at_once` and `test_the_last_retried_card_takes_its_group_with_it` differ from the start of the milestone only in what they wait for; every assertion is there.
- **The new tests hold content, not presence:** Coming's exact lines, the stored rows, the page's address after two sends, one wrapper, one form, one Coming.
- **Layout:** `test_the_desk_page_lays_out_at_phone_and_display_sizes` passes with Coming inside the wrapper, at both sizes.
- The dashboard is English only: no French in this milestone.
- Not checked: nothing ran on a real phone, and I took no screenshot.

**Score: 6 of 10.** The feature is right, small and well tested as merged. It took six developer attempts, two escalations and six days to land 20 lines, and half of that was the lead's doing.

## Backlog

Two nits added to `docs/backlog.md` (F3, F4).

## Workflow observations (Factory)

- **Flow:** one developer ticket, two sessions, six attempts, one direction, two escalations (a requeue, then a finish). No stop for the owner, no ADR. No checkpoint, since the only merge was the lead's.
- **Qwen:** 0/1 at difficulty 3. Four attempts stopped with no edit after 10 minutes of reading and two timed out, at about 101k tokens a step. Where it edited, it replaced the form with `fetch` and `replaceChild`, which htmx never binds, so the second plant left as a plain `GET`; and it removed the assertions that showed it from two existing tests. Its own second-plant test seeded the first idea in the database, so it never sent twice from one page.
- **The lead:** three mistakes, all at plan and queue time. The ticket was queued on a red main; it wasn't re-read when F48 changed the form it describes; and the direction of 2026-10-10 could not help while the gate failed on main. Each has its line in `lead.md` or `docs/task-writing.md` now, and `f106-06` turns the first into a check.
- **The escalation that finished it** did what owner.md asks: it fixed the cause, restored the weakened tests, and made the second-plant test one that fails any re-draw htmx doesn't bind. It could not write its lesson where developers read it; a review or a terminal session has to carry that last step, and this one did.
- **What to change:** nothing new beyond the three items under "What next".
