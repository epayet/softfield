# ADR 22: One visible queue: the runner queues every job before it runs it

- **Status:** Proposed (drafted by the lead, 2026-10-04)
- **Date:** 2026-10-04
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:**
  - [ADR 12](12-junior-feedback-and-checkpoints.md) items 6 and 8 (directions and checkpoints become queued jobs);
  - [ADR 16](16-claude-window-and-named-milestones.md) item 3 and [ADR 15](15-allowance-aware-routing.md) item 5 (the reserve questions become switches);
  - [ADR 17](17-always-on-factory.md) (a due review is a queued job);
  - [ADR 20](20-planning-room.md) item 1 (planner jobs take their place in the same order).
- **Evidence:** the owner's notes after F3 and F4 (2026-10-04): "are the reviews still happening every 2 dev tickets? … when does replan happen? is it a ticket? it'll be easier to visualise if everything is a ticket queued"; "the runner should be just running jobs, and most work should be visible there, an escalation, a review, a replan, an answer to my question … the more it's hidden away in the runner logic, the harder"; "Use reserve should be a toggle I can turn on off".

## Context
Today the factory has three kinds of work, and only one of them can be seen ahead of time:
- **Tickets** (`tasks/ready/`) are visible: the queue, the line's hopper and `--dry-run` list them in run order.
- **Support jobs** are triggered from inside the runner's code and appear only once they run:
  - checkpoints (after every 2 developer merges, `note_merge` in `runner/loop.py`);
  - directions (before a ticket's last attempt, inside `run_task`);
  - escalations (after it, in `work_queue`);
  - the due review (f4-20, `_due_review`; the only one already shown ahead, as "review F3");
  - parked jobs (`state.json`'s `parked`, resumed by `_resume_support`);
  - the stand-in checkpoint.
- **Owner questions** (the week's reserve, the 5-hour window) exist only in the console, as a y/N with a timeout, once per command. F5's f5-10 adds Yes/No buttons to the same question.

The order between them is spread across `work_queue`, `_resume_support`, `lead_work_ready`, `_next_task` and `at_five_hour`, so neither the owner nor the dashboard can say what runs next or why. Parallel work (a later ADR) needs the same thing: one list of jobs that several lanes take from.

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ Triggers queue, they don't run.**
   - Every rule that today starts a support job instead adds a row to a new `work_queue` table in the metrics database, with:
     - its kind;
     - its subject (a ticket or a milestone);
     - its reason in plain words ("after f5-08 and f5-09 merged");
     - when it was queued;
     - `not_before` (a reset time, for a parked job);
     - the job that ran it.
   - The kinds:

     | Kind | Queued when | Reason, e.g. |
     |---|---|---|
     | `checkpoint` | every `checkpoint_every` developer merges (unchanged) | after f5-08 and f5-09 merged |
     | `review` | a milestone's tickets are all done (unchanged) | F5's 17 tickets are done |
     | `direction` | before a ticket's last attempt (unchanged rules) | f5-09 failed twice: ruff, then tests |
     | `escalation` | after the last attempt, BLOCKED.md or pre-flight | f5-09: tests still failing |
     | `planner` | the owner sends a message (F6) | your message on F7 |

   - **Tickets stay files.** They are planned and approved work, with pre-flight and gates, and `tasks/` stays their source of truth. The queue reads them as they are; it doesn't copy them.
   - A ticket's attempts 1–3 stay one ticket job. A direction or escalation is queued at the front, and the ticket waits behind it, as today.
   - Replans stay lead tickets, written at planning (lead.md "Replans"), or proposed from the planning room (F6).
2. **⚑ One function picks the next job** (`runner/dispatch.py`, pure: it takes the queue rows, the ready tickets, the windows and the time, and returns the job and why):
   - First by kind: `planner` › `escalation` › `direction` › `checkpoint` › `review` › lead ticket › developer ticket.
   - Then by priority (a ticket's, f5-06), then by age.
   - A job whose agent can't run now (a limit, the owner's 25%) is skipped with its reason, and the next one is taken. This keeps ADR 16 item 2's "lead work first, developers meanwhile" without a separate path.
   - Parking becomes a queue row with `not_before`, replacing `state.json`'s `parked`. The work kept on a branch and the session to resume are unchanged.
   - No AI in it; `--dry-run` prints the same list.
3. **The queue is what the dashboard shows.**
   - The Overview's queue and the line's hopper list every queued job, tickets and support jobs alike, in the order they will run, each with its kind, subject, reason and what it waits for (a reset, a dependency, you).
   - A finished job's row links to its job page.
4. **⚑ The reserve questions become two switches** (amends ADR 16 item 3):
   - **"Let the factory use the week's reserve"** and **"Let the factory use your 25% of the 5-hour window"**, each beside its meter on the allowance panel.
   - Each switch is a `reserve` request (subject `week` or `five_hour`, value `on` or `off`, ADR 18). `runner reserve week|five-hour on|off` does the same from the console.
   - It stays as set until the owner changes it; it no longer resets per command.
   - **Off** (the default) behaves as today's unanswered question:
     - a lead ticket at the week's reserve waits for the owner;
     - at the 5-hour line, it parks until the reset.
   - **On** behaves as a yes.
   - The runner no longer asks y/N in the console. The Needs-you item for the week's reserve says which switch would let the ticket run.
   - f5-10 (the Yes/No buttons) is rewritten as the switches.
5. **Pause is a state of the picker** (f5-18, as written): while paused, the pick returns nothing and says "paused by you". A running job is never stopped.
6. **Nothing else changes:** caps, attempts, directions and escalations per task, `checkpoint_every`, review rounds, routing and the Claude rules stay as they are. This ADR changes *where* the decisions are made and *what you can see*, not what runs.

## Consequences
- **Good:**
  - The owner can answer "what runs next, and why?" from the phone, for every kind of work.
  - The checkpoint rule ("every 2 developer merges") shows up as a queued item with its two tickets.
  - The order lives in one tested function instead of five.
  - Parallel lanes (the next ADR) take from this queue.
- **Cost:**
  - A refactor of the runner's main loop (`work_queue`, `run_task`'s direction and escalation calls, `note_merge`, parking): about 5 lead tickets, test-first, in a milestone of their own after F5. The dashboard's queue view is one or two tickets on top.
  - The runner is protected code, so all of it is lead work.
- **Risk:** a bug in the picker stalls or reorders the factory. Mitigation: `--dry-run` prints the picker's choice and reasons; the first tickets keep the existing order exactly (a test replays F4's session logs' order), and only then add the new kinds' rows.

## Open questions
1. **One switch or two?** The questions are separate today, and a yes to one doesn't answer the other. Two switches keep that. One "use the reserves" switch is simpler if you'd always flip both together.
2. **The kind order.** It puts a due checkpoint before the next ticket, as today. Should a review wait until no ticket of another milestone is ready? Today it doesn't wait.
3. **F5's order:** f5-06 (priority pick) and f5-18 (pause) still make sense as written and are kept: they become parts of the picker. Only f5-10 changes.
