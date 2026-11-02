# ADR 29: The lead looks at a blocked ticket before the owner does

- **Status:** Accepted (by the owner, 2026-10-13)
- **Date:** 2026-10-12
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 12](12-junior-feedback-and-checkpoints.md) item 10 (a ticket past its limits goes to `.softfield/tasks/blocked/` and waits for the owner) and [ADR 20](20-planning-room.md)'s replan (it may change only its card's tickets in `.softfield/tasks/ready/`).
- **Evidence:** F106 (2026-10-12): the owner asked where blocked tickets go for them to review. Four were blocked, all the lead's own tickets (f21-01, f21-02, f21-03, f31-03), none on the desk, and no command or button brings one back. The owner's rule: "every problem comes with a suggested fix" (owner.md, 2026-10-04).

## Context
- A blocked ticket is work that failed past every limit: a lead ticket whose checks failed, or a developer's ticket after two escalations. Its branch and logs say why; reading them is the lead's work.
- Today it waits for the owner with a one-line reason ("check-all failed; the work is on task/…"), which the owner can't act on without a terminal session.
- A planner job already drafts fixes on a card's plan branch for the owner to approve. It can't touch a blocked ticket: a replan only reaches `.softfield/tasks/ready/`.

## Decisions (⚑ = deviates from an earlier decision)
1. ⚑ **When a ticket is blocked, the runner queues one planner job on its card's thread.** Its message is the runner's, not the owner's, and the thread shows it so: the ticket, the reason, the branch and the logs to read.
2. **The lead replies with what went wrong and a fix,** in plain words, as a replan the owner approves or sends back: the ticket reworked, split, or set aside.
3. ⚑ **A replan may bring back its card's blocked tickets.** On the plan branch it may move `.softfield/tasks/blocked/<card>-*.md` to `.softfield/tasks/ready/` (reworked; it must pass pre-flight) or to `.softfield/tasks/later/`. Never another card's.
4. **One look each time a ticket is blocked.** A ticket goes back to the queue only when the owner approves or presses "Try again", so the lead can't loop on its own.
5. **Under the usual limits.** The look is a planner job like any other: on Opus, parked at Claude's limits, run under the reserve.
6. **A bug ticket has no card,** so no look: it shows on the desk with "Try again" and "Set aside" only.
7. ⚑ **A check that fails on main too blocks no ticket** (amends ADR 12 item 9: "a lead ticket that fails is blocked"). When a lead ticket's `check-all` fails, the runner runs the failed checks on main. If main fails them all, the ticket keeps its place and its branch, the runner takes no other lead ticket, and the owner gets one item naming the failing check and the ticket that would fix it. No check is skipped: a ticket still merges only when all of `check-all` passes. Evidence: on 2026-10-12 one stray file on main blocked four finished lead tickets in a row (f21-01, f21-02, f31-03, f48-01), about $10 of Opus, with nothing wrong in any of them.

## Settled with the owner (2026-10-12, terminal session)
- **The lead looks first** (items 1 to 6), not the buttons alone.
- **Item 7 stays in this ADR:** one acceptance covers the look and the red main.
- **Item 7 is built before the look** (f106-06 before f106-04), so a failing main never costs one look per blocked ticket.

## Alternatives turned down
- **The buttons only** ("Try again", "Set aside"; F106 tickets 01–03): cheaper, but the owner gets a failure with no fix, and trying again as written often fails the same way (f21-03 "changed nothing").
- **A third escalation instead of blocking:** ADR 12's limits exist because more tries on the same ticket rarely pass. The look doesn't retry; it reworks the ticket.
- **The lead requeues on its own:** nothing reaches the queue without the owner's approval (ADR 20).

## Consequences
- Each blocked ticket costs one planning reply on Opus. Blocks are rare (six in the repo's history, four of them in the last days).
- The owner's desk item for a blocked ticket becomes a proposal to approve, with the raw failure a link away.
- A card whose thread is archived opens again when its ticket is blocked.

## What doesn't change
- The limits of ADR 12 item 10, and that a blocked ticket's dependants pause.
- Nothing merges or queues without the owner.
