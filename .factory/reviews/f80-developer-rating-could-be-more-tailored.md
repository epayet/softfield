# Review: F80, how each agent does by kind of work

- **Status:** review round 1 done. Two nits are fixed in the review, and one runner fix waits as a lead ticket (f80-02). Waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
The Agents page has a new panel, **By kind of work**, right after Efficiency. For each agent it shows two rows: **Pages** (tickets that touch a template, CSS or JavaScript file) and **Code, no pages** (the rest). Each row has:
- how many tickets the agent played;
- a bar in the agent's colour for how it actually did (merged first time counts 1, merged later ½, not merged 0);
- a dot for what its rating expected on those same tickets;
- a word: "better" or "worse" when the two are more than 5 points apart, else "as rated".

A row with fewer than 3 tickets says "too few to say" and is drawn faded. The milestone filter at the top limits the panel, as it limits the ratings chart.

As planned, the rating itself is unchanged and routing doesn't read the panel. It shows whether one rating per agent hides a real gap. Today's answer on softfield: Qwen is as rated on pages (56% against 58% expected, 114 tickets) and does better than rated on code without pages (74% against 68%, 60 tickets). That's not yet the 10-point gap the card set before a rating per kind is worth an ADR.

### 2. How to test it yourself
1. On the laptop, open **Agents** on softfield. Below Efficiency you should see "By kind of work" with two rows for local-qwen3.6-35b-a3b: Pages about 114 tickets, Code about 60, with a green bar for Qwen.
2. Read the last column. Qwen's Code row reads "+6 better" and its Pages row "−2 as rated". Claude Opus's rows read "+3 as rated" and "+5 as rated", each signed.
3. Look for faded rows: claude-sonnet's Code row (2 tickets) and ollama-nemotron-3-super's Pages row (1) say "too few to say".
4. Pick a milestone in the filter. The panel shrinks to that milestone's tickets. A milestone with no coding games shows a single line: "No coding games to show."
5. Switch the theme with the top-bar button: bars, dots and words stay readable in both.
6. On the phone, open the same page: the table scrolls sideways inside its panel, like the others.

### 3. Left for later
- **A rating per kind, in routing:** as planned, an ADR only once a second developer is in `[roles] developer` and the panel shows a 10-point gap over 20 tickets or more in one kind. Not yet.
- **A rating per project:** travel-companion's larger gap may be the project's difficulty scale. Weigh it in the same ADR.
- Nothing new in `docs/backlog.md`.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-27, night run: the local model built f80-01 on attempt 1 (72 minutes, 10.1M tokens in). Every gate passed except the whole test suite, which failed on a test that main itself was failing at the time (`bug-03`'s card check). Attempt 2 (13 minutes) saw the failure was outside its files and blocked, as developer rule 11 says.
- 2026-10-27, 19:13: about 16 hours later, once Claude's allowance let escalations run, Opus finished it on the branch in 6 minutes ($1.56). It removed a mock-up note the developer had copied onto the page, made a game with no difficulty skip as the ticket said, simplified the query and added three tests.
- Review, 2026-10-28: fixed two small display points (below) and filed f80-02 for the runner.
- Lessons:
  - **A red main still costs a developer its attempts.** F106 already holds lead tickets while main is red, but not developer tickets. Here that meant two attempts, a 16-hour park, an Opus escalation, and two "not merged" games against Qwen's rating for work that was right. The same red test cost another ticket an escalation that evening. What changes: f80-02 (a lead ticket, runner code) holds the developer's ticket the same way.
  - **A mock-up's notes to you aren't part of the page.** Qwen copied "▲ new bay" onto the page. Now an example in `docs/agents/developer.md`.
  - **The panel already answers the card's question.** One rating hides no gap worth splitting for Qwen on softfield yet. The gap is about the project, not the kind.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:**
  - Let f80-02 land before the next long night run. A red main is the one failure where a developer is blamed for someone else's test.
  - Check this panel when a second developer joins `[roles] developer`. That's when a rating per kind could change a pick. Text to plant if you want a reminder: "When a second developer is in the roles, look at By kind of work on the Agents page and decide whether a rating per kind is worth an ADR."

### 7. What clogged the factory line
- **Parked for Claude: about 15.8 hours** (2026-10-27 03:25 to 19:13). The escalation waited while Claude's allowance went to planner jobs (four rounds of them that day, each ending "parked"). To unclog it: f80-02, since this ticket shouldn't have needed an escalation at all.
- **Failed attempts on a red main: about 1.4 hours of the local model** (72 + 13 minutes). To unclog it: f80-02.
- **Waiting before the start: about 18 hours** (plan 2026-10-26, first job 10-27 02:00), behind cards above it on the board. To unclog it: nothing, that was the board's order.
- No stops for you on this card.

## What was built
- `factory_dashboard/agents.py`: `work_kind(files)` (D1), `by_kind_data(conn, project, milestone)` (D2, D3). It reads the coding rows of `rating_changes` whose result is one of the three ticket results, joined to their ticket's files and difficulty (corrected when set; games with no difficulty are left out), and groups them by agent and kind. Each row has a count, score and expected (whole percent), the gap and its words. `agents_page` passes the result to the template.
- `factory_dashboard/templates/agents.html`: the `#by-kind` panel after Efficiency, with a gauge per row (fill = score, mark = expected), a key, and a one-line empty state.
- `factory_dashboard/static/dashboard.css`: the panel's styles, from tokens only (hazard stripe on the header, a corner tick in ink, the agent's colour through `--who`).
- Tests (`tests/factory_dashboard/test_agents.py`): the kind rule, each result's score, bench and finding games excluded, the three gap words and "too few", the milestone filter, the empty line, separate rows per kind, the corrected difficulty. Opus added: the mixed three-game Pages row against `expected`, the skipped game, and the row's text and colour on the page. The review added the signed "as rated" gap and the colour of a model's next version. No existing test was edited.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | ticket (lead) | A developer attempt failing only `all-tests` on a test main fails too costs attempts, an escalation and rating games; F106's main-red guard holds lead tickets only | [f80-02-red-main-spares-the-developer](../tasks/ready/f80-02-red-main-spares-the-developer.md), `agent: lead` (runner code) |
| F2 | nit | claude | An "as rated" gap above zero showed unsigned ("3 as rated") beside "+6 better" | Fixed: signed in the template; new test |
| F3 | nit | claude | Agent colours keyed on full ids, so a model's next version (or nemotron-3-ultra) would draw muted | Fixed: matched by family prefix in `_agent_token`; new test |

Checkpoint verdicts: none. No checkpoint ran: the lead finished the only ticket.

Score: 8/10. The panel does what D1–D3 say, matches the mock-up, follows the theme and answers the card's question on live data. The local model's code was close. What it missed (a note copied from the mock-up, one skipped Done-when line) the escalation fixed. The cost went to the factory, not the work: a red main turned a first-time pass into a 16-hour escalation.

Checked and fine:
- `.js` doesn't catch `.json`.
- Scores and gaps come from rounded percentages, as D2 says ("whole percentages").
- Expected uses `runner.ratings.expected` with the game's own `before`.
- The page's SQL is parameterised.
- Light and dark both come from tokens.
- The mock-up note is gone.

Tests: `tests/factory_dashboard/test_agents.py` passes (35), and ruff and mypy are clean on the changed files. The whole `tests/runner tests/factory_dashboard` run passed 2,719 tests and failed none. The time limit stopped it in its last file, `test_timeline.py`: its 10 tests show as errors at setup, from the stop signal. That file passes on its own (15 tests). The rest of this diff range belongs to other milestones (F59, F68, F69, F81, F82, F84, F136, F139, F142, F143, F164, F173) and their own reviews.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Nothing new.

## Factory
- **Flow:** one developer ticket. It was escalated after two attempts, parked about 16 hours for Claude, and finished by an Opus escalation. No checkpoint, no stops for you.
- **Models:**
  - Qwen3.6 35B: about 1.4 hours, 11.2M tokens in. Its build was right on the first attempt but for two small points.
  - Opus: $1.56 for the escalation. The plan and review costs are in the numbers below.
- **What to change:** f80-02. Also, the planner jobs on 2026-10-27 used enough of Claude's allowance to park escalations four times that day. That's for the factory's own review rather than this card. It's a known trade (ADR 20 item 2: planning runs under the reserve).

<!-- runner report -->
<!-- /runner report -->
