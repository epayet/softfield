# Milestone F31: Proposals close the loop

> **Status: planned** (2026-10-07, with the owner, in a terminal session). **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-10-07 as "when i click on approve plan it looks like i can keep clicking on it"; grown the same night to every gap around proposals.

## Notes
when i click on approve plan it looks like i can keep clicking on it

The owner, 2026-10-07: "proposals exist after a thread suggests actions from a discussion. They have a state open, accepted. It should be clearer that when I approve a proposal, then the thread is not on my desk anymore. I can still click on accept proposal even though I accepted already. I also want to reject. The outcome of the proposal could be clearer, perhaps color coded whenever an ADR or a ticket is made. A lot of the points are just for information rather than action, so it shouldn't be a box." Also folded in from notes the runner refused for their length (plants 27, 50, 60): "the only way for me to agree is to comment 'agree'"; "there is the raw text and then small boxes… I tend to just scroll down and ignore the raw text"; "it took me a long time to realise there was a proposal section on the right". And: "instead of asking me for a title, I should just type the content and it gets a relevant title generated later."

### From F45: When I approve a plan it should close the related conversation (merged by the owner on 2026-10-08)
(none)

### From F47: when i a'pprove a plan and refresh the page (merged by the owner on 2026-10-08)
it doesn't look like i approved, i can click th ebutton indefinitely

## Outcome
- **Approving clears the desk:** once every proposal in the lead's latest reply is approved, accepted, merged or rejected, the thread is archived with the reason, and leaves "Your answers wanted" and Needs you.
- **A proposal says where it stands:** open, on its way, approved (with the runner's result), rejected, sent back or replaced, on its review page and on its thread. Its buttons show only while it's open, and each is pressed once.
- **Reject = won't do.**
- **A reply reads at a glance:** information points are plain lines; action points are boxes coloured by what they lead to (an ADR, a plan's tickets, a mock-up), and "What to do now" sits right under the lead's latest reply, with Approve and Reject.
- **Nothing of the owner's is lost unseen:** a refused note waits on the desk with its words until the owner tries again or dismisses it.
- **Plant is one box:** the owner types the note, and the lead names the card in its first reply. Nothing is refused for its length.

## Decisions
- **D1 Settled (owner, 2026-10-07):** a proposal is settled only by the owner's act: an `approve_plan`, `accept_adr`, `plant` (a seed) or `reject` about it that worked (f6 D6's `_about`), or a merge applied. Silence settles nothing. When every proposal of the thread's latest lead message that lists proposals is settled, the runner adds one lead line ("Approved by the owner on 2026-10-08: queued f13-01-…"; "Rejected by the owner on …: won't do") and archives the thread with its reason (`approved` or `rejected`), resolving its `planning` item as an archive does. An ADR accepted while its plan is open settles nothing more. A thread with no proposals, or one the owner leaves unanswered, stays until the owner archives it. A message from the owner opens an archived thread again, as today. The general thread too.
- **D2 Reject (owner, 2026-10-07: "won't do"):** a request `reject`, subject `<thread>/<proposal id>`, no value.
  - On a card's `adr`, `mockup`, `plan` or `replan`: the plan branch goes (every draft on it), so every draft-carrying proposal of that set is rejected with it. When the card has no ticket in `tasks/` and isn't building, its doc is `git rm`ed in a commit of its own (`F31 rejected by the owner`) and it leaves the board, as `drop_seed` does. A card with tickets (a rejected `replan`) keeps its doc and state.
  - On a `merge` or a `seed`: nothing is drafted; only that proposal is settled.
  - Refused, nothing changed, for a proposal not in the thread's latest set, or one already settled.
- **D3 One state, from the server:** `runner/planner.py` says a proposal's state from the requests about it since the lead's message: `open`, `on its way` (a request pending), `approved`, `rejected`, `sent back`; the dashboard adds `replaced` (not in the thread's latest set). The desk, the thread and the review page all read it. Buttons show only while `open`; after a press, the dock is re-fetched (`hx-select`), as F13 D1 and f6-21 do, and shows the dashed orange "on its way" box with the request's status. Replaces F31's first draft (D1–D3 on `plan/f31`, dropped).
- **D4 Points carry an outcome:** each point in the reply block gets `outcome`, one of `info`, `ticket`, `adr`, `mockup`, `roadmap`, `merge`, `question`, and `proposal` (an id from the same block) when it leads to one. A point without one (every reply before this) shows as today. `info` is a plain numbered line with a small Comment… link; the others are boxes with a left edge in their proposal kind's colour (`_KIND_COLOR`), `question` in the hazard colour.
- **D5 What to do now:** on a thread, the open proposals sit right under the lead's latest reply (above the reply box, on a phone too), each with its state and, while open, Approve (or Accept ADR, Plant it, the merge's Approve) and Reject. The aside goes. After the mock-up, which the owner OKs first.
- **D6 The lead's words:** at most two lines of prose before the points; every card named with its title ("F22, Archive at the bottom"), never a bare number; a reply to "agreed" or "go" with nothing new says only that the plan waits for Approve, in one point. Every F-number in a thread is tappable for its card's title (D5's ticket).
- **D7 Plant is one box (owner, 2026-10-07):** a `plant` request's value is `{"text", "area"}`; an old `{"title", "thoughts"}` still works. The card's key and slug come from the text's first words and never change; its heading, until the lead names it, is the first words cut at a word under 60 characters; the whole text is its Notes. Plant files a seed and Plant and ask the lead also sends it (ADR 20 item 8, 2026-10-08); the lead's first reply on a card still `idea`, whenever it comes, gives a short `title` in the reply block, and the runner rewrites the card's heading alone on main, in a commit of its own (`F32 named by the lead`); the file name stays. Nothing is refused for its length (the 20,000-character cap on the text stays; the 120-character title refusal went on 2026-10-08, a long title cut at a word with the rest joining the thoughts).
- **D8 What approving changes, with who builds it:** f6-24's rows each show the ticket's agent (lead or developer) and difficulty, coloured by their word (added, changed, set aside, removed).
- **D9 Nothing of the owner's is lost unseen (owner, 2026-10-08: "ensure notes don't get lost, or make it obvious on the ui if they do, i had no idea"):** seven plants were refused on 2026-10-07 and nothing showed it. A refused `plant`, `plan_message` or `send_back` waits in a desk group, "Didn't go through", first and counted, with the words, the reason, Try again and Dismiss, until the owner acts.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | settle-and-reject | L | 8 | – | D1, D2, D3's state function |
| 02 | review-states | D | 5 | 01 | D3 on the review page and the thread's cards; Reject; D8 |
| 03 | point-outcomes | L | 6 | – | D4's block and D6's prompt; D7's `title` |
| 04 | what-to-do-now | D | 6 | 02, 03 | D4 and D5 on the thread, after the mock-up (in `tasks/later/` until then) |
| 05 | plant-one-box | L | 6 | 03, f13-01, f14-01 | D7 |
| 06 | refused-on-the-desk | L | 6 | – | D9; first of the card |

## Done when
- Approve a card's plan from a phone: the button goes at once, the dock says it's on its way, then "approved · queued …"; the thread leaves the desk and shows under Archived as approved.
- Reject a seed card's plan: nothing queued, the branch and the card are gone, the thread is archived as rejected.
- A new reply shows information points as lines and actions as coloured boxes, with "What to do now" under it.
- Plant a 300-character note: it's planted, and the lead's reply gives the card its title.

## Not here
- F16 (an answered thread leaves the desk while the message waits) and F30 (latest answer first) change the same pages; each stays its own card.
