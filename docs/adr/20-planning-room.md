# ADR 20: The planning room: plan with the lead from the dashboard, asynchronously

- **Status:** Accepted (by the owner, 2026-10-03)
- **Date:** 2026-10-03
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 16](16-claude-window-and-named-milestones.md) items 1–2 (who goes first, for planner jobs); [ADR 19](19-feature-board.md) item 5 (planner questions become this room); [ADR 18](18-dashboard-writes.md) (new request kinds)
- **Evidence:** the owner's planning sessions of 2026-10-02/03 (one long Claude Code chat: answers with actions, mock-ups, questionnaire reviews of ADRs, tickets on approval). The owner's goals and choices (2026-10-03, `docs/roadmap.md` "The planning room"). The mock-up: <https://claude.ai/artifact/UNELSzF5iF5RccjVJiWZzx>, sources in `docs/milestones/planning-room-mockup/`.

## Context
The owner wants to do from the system what those sessions did, asynchronously, with a good UI:
- plant ideas;
- ask about them;
- get answers with suggested actions;
- review ADRs, mock-ups and plans questionnaire-style;
- approve tickets.

All of it without checking first whether the factory is busy, whether the lead has credits, or what is waiting for them. Planning is the owner's highest priority.

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ Planner jobs go first** (amends ADR 16 item 2). A new role, `planner` (Opus). At each pick, an open planner request goes before every other lead job; it never stops a running job. The runner does it, one job at a time, beside developer jobs once work runs in parallel.
2. **⚑ Planning may use the whole 5-hour window** (amends ADR 16 item 1 for this role). It's the owner's own work, so the 25% kept for the owner is theirs to plan with. The factory still stops at 75%.
3. **Threads:** one per card, plus one general thread for ideas without a card (which can become a seed). A thread continues the same Claude session each turn (`claude -p --resume`), so it stays small. Its messages are stored for the UI.
4. **Replies are numbered points:** each with a title, an answer and a suggested action, written as a JSON block the runner checks before recording. The text around them is free.
5. **⚑ Every point counts as agreed by default.** The owner comments only on what they want to change or question, plus a free message. Sending is one request. The next planner job answers the questions first, then revises.
6. **The lead only proposes:**
   - ADR drafts, mock-ups (HTML files in the repo, shown on the dashboard), milestone docs and tickets are drafts on the card's `plan/<card>` branch.
   - Each proposal is listed with its key points, for the same questionnaire review.
7. **Approving is a request** (ADR 18). "Accept ADR" and "Approve plan" make the runner merge the card's drafts (docs and tasks only, with every ticket pre-flighted) and accept the ADR. Only then do tickets reach `tasks/ready/`.
   - **The thread goes into the repo with it** (owner, 2026-10-07, F20): the approval's commit also writes the whole thread to `docs/planning/<card key>.md`, so the why sits beside the decision. A thread that is never approved stays in the database (backed up daily, ADR 13 item 1).
8. **Planting needs no Claude:** "Plant it" is a request. The runner writes the seed card (`docs/milestones/<key>.md`, next free key, the owner's words) at its next pick.
   - **And the lead answers it** (owner, 2026-10-07): a planted idea is often a question. The owner's words are also the card thread's first message, so a planner job answers them at once. The card still lands without Claude; at a limit only the answer waits.
   - **Only when asked** (owner, 2026-10-08: "I want the ability to control when I send it to the lead"): the form has Plant (a seed that waits in Seeds until the owner writes on its thread, "Send to the lead") and Plant and ask the lead (the above). A plant request carries `"ask": true` for the second; without it, nothing goes to the lead.
9. **One list of what waits for the owner:**
   - **The planning page's desk** is the full view.
   - **The Overview's Needs you** shows its count and top items.
   - **The top bar** shows "Planning · N".
   - **A notification** comes when a reply or proposal lands.
   - **Archiving a thread** (owner, 2026-10-07) takes it off all of these: its Needs-you item goes, and the Planning page lists it under Archived, the most recently archived first. Unarchive, or any message from the owner on it, opens it again.

   "The factory now" says what runs, and when the next reply will come.

## Consequences
- The owner plans whenever they like, from a phone. When Claude is at its limit, messages wait and are answered at the reset.
- Planning spends Claude's window before factory work does. A busy planning day slows lead tickets, which is the owner's priority.
- The plan branch keeps unapproved drafts off main; approval keeps git to one writer.
