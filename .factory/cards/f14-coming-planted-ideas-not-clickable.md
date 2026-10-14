# Milestone F14: Coming planted ideas not clickable

> **State:** done · **Priority:** 1 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-14. Base: git tag `f14-coming-planted-ideas-not-clickable-start`. Report: [`.factory/reviews/f14-coming-planted-ideas-not-clickable.md`](../reviews/f14-coming-planted-ideas-not-clickable.md).
> Planted by the owner on 2026-10-07.

## Notes
They look like I can click on them to edit or cancel them but I can't. Ensure this is part of the plan for editing/cancelling coming ideas

The owner, 2026-10-07: "i want to be able to edit or cancel something in the queue that hasn't been sent yet".

## Expected outcome
A plant or a message still in "Coming" (the runner hasn't taken it at a pick) can be tapped, edited or cancelled. The change shows at once, on its way like any request, and the runner applies it before anything else at its next pick. A change that arrives too late (the request was already taken) says so plainly.

## Done when
- Tapping a waiting plant on the desk opens it with its title and thoughts, and **Save** and **Cancel it**.
- A waiting message on a thread has **Edit** and **Cancel it** the same way.
- After either, the row shows what was asked at once (the new words, or struck through with "cancelling at the runner's next pick"), with the dashed orange edge, and can't be changed again until the runner has taken it.
- At the next pick, a cancelled plant makes no card and no Opus reply; an edited one is planted with the new words.
- A change that comes too late finishes as "too late: already planted" (or "already sent"); the dashboard shows that result.

## Decisions
- **D1 One new request kind, `change`.** Its subject is the id of the request it changes; its value is the new value (a plant's `{"title", "thoughts"}`, a message's `{"text", "comments"}`), or `{"cancel": true}`. The dashboard still only adds a row to `owner_requests` (ADR 18 item 2): it never edits or deletes one, so the runner stays the one writer of what happens, and there's nothing for the two to race over.
- **D2 Changes go first.** `apply_requests` applies every open `change` before the other requests of the same pick. If its target is still open: a cancel finishes the target as "cancelled by you"; an edit replaces the target's value, and the target is then applied as usual in that same pick. If the target is already done, the change finishes as "too late: …" and does nothing. A change doesn't commit, so it never waits for main.
- **D3 Plants and messages only,** the two texts in Coming. A pause or a resume is applied within 5 s already; other requests are one-tap buttons the owner can undo with the opposite button.
- **D4 Before the pick only.** Once a message is taken, it's on its thread and its planner job usually runs at that very pick (queued jobs go before tickets). Editing a stored message or stopping a queued planner job is left out; a planted card can already be removed with Drop (f6-17).
- **D5 The rule "stops being editable" (owner.md, 2026-10-07) becomes "editable until the runner takes it".** What was asked still shows at once, on its way; a change waiting on it is itself on its way and can't be changed again.
- **This supersedes** the earlier answer on this thread that an on-its-way row should simply lose its link look: it now opens for real.

## Tickets
1. `f14-01-change-request` (lead: `runner/` is protected): the `change` kind in the runner and in the dashboard's accepted kinds.
2. `f14-02-coming-editor` (developer): tap a waiting plant on the desk to edit or cancel it; Coming and the Now page show the change at once.
3. `f14-03-edit-waiting-message` (developer): Edit and Cancel it on a waiting message on its thread.
4. `f14-04-failed-edit-shows-on-desk` (lead, from the review's F1): an edit that came too late or was refused shows under "Didn't go through" with its words, until dismissed.
