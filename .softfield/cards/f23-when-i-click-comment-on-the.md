# Milestone F23: when i click comment on the planning desk ticket, i want it to focus on the text box

> **State:** done · **Priority:** 2 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-16. Base: git tag `f23-when-i-click-comment-on-the-start`. Report: [`.softfield/reviews/f23-when-i-click-comment-on-the.md`](../reviews/f23-when-i-click-comment-on-the.md).
> Planted by the owner on 2026-10-07.

## Notes
i currently need to click on both comment and then cilkc on the box to start typing

## Plan
**Expected outcome:** tapping "Comment…" under a point of the lead's reply on a planning thread (`/planning/<card>`) opens the box with the cursor in it, so you can type straight away (on a phone, the keyboard comes up).

**Done when:**
- one tap on a point's "Comment…" opens its box and puts the cursor in it;
- a second tap closes the box, as it does today, and keeps what was typed.

**How to test:** open a planning thread that has a reply with points, tap "Comment…" on point 2 and type at once, without tapping the box. Try it on the phone too.

**Decisions:**
- The cause: the thread page (`factory_dashboard/templates/thread.html`) opens the box with a plain `<details>` that nothing focuses. The proposal review page (`factory_dashboard/templates/proposal.html`) already focuses its box on "Comment…", so only the thread page changes.
- Keep the `<details>`, but open it from the tap and focus the box in the same tap. Focusing later (on the `toggle` event) works on a computer but on an iPhone puts no keyboard up. The click is caught on the document, so a conversation reloaded in place still works.
- One developer ticket: small, unprotected, and `proposal.html` is the example.

**Tickets:** `f23-01-comment-focus`.
