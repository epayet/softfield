# Milestone F62: A review on Now says which card it reviews

> **State:** ready · **Priority:** 90 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
(none)

### From F65: The lead is reviewing stuff but I don't know what it is it… (merged by the lead on 2026-10-08)
The lead is reviewing stuff but I don't know what it is it doesn't tell me. I believe this is planned, verify that it is and prioritise it

## What happens today (from the code and the database, 2026-10-26)
- A review, a planner reply and a checkpoint are jobs with no ticket. Each job row does carry its card (`jobs.milestone_id`; `running_jobs` in `factory_dashboard/overview.py` already reads it as `milestone`), but nothing shows it: Now prints a ticket link only when there is one (`_partials/running.html`), so job 1353 read "attempt 1 · claude-opus · review · job 1353 ›" while it reviewed F158.
- The same gap in four more places: the top bar ("Running: review, job 1353", `factory_status` in `factory_dashboard/app.py`), the Projects page's running line (`running_now`, `projects.html`), the Planning room's running line (`planning.html`, `planning.py`'s `job.ticket or job.role`) and the Jobs list ("–" in the Ticket column).
- Next in line names a due review "review F68 · a batch" (the due-review rows, `"kind": "batch"`, in `factory_dashboard/line.py`, drawn in `_partials/queue.html`): the key but not the card, and "a batch" means nothing to the owner.
- Not planned anywhere: F152 (A done card says where its review is) puts "Review running" on the board's card, not on Now; F33 (Now says how long) adds time lines to Now. Neither names the card.

## Outcome
Whatever the lead or Claude is doing without a ticket, Now, the top bar, Next in line, the Projects page, the Planning room and the Jobs list say which card it works on, by key and title, and in one line what the job is for.

## Done when
- While a review runs on a card, Now shows the card's key (linked to its page), its title, and "The lead reads what F158 built, before it's yours to sign off"; the top bar reads "Running: softfield · review F158".
- A due review in Next in line reads "review F68" with F68's title and "the lead reads what it built", not "a batch".
- A planner reply and a checkpoint name their card the same way; a job with neither ticket nor card (a probe) shows as today.
- To test: open the Overview while a review or a planner reply runs (one runs at every reply on the Planning room), and on a phone.

## Decisions
- **D1 One function names a job's card.** `job_card(conn, job) -> (key, title) | None` in `factory_dashboard/overview.py`: the short key upper-case (`short_key`) and the title from the card's doc heading, as the Planning room's card title does (`milestone_doc(...)["title"]`, `factory_dashboard/planning.py`), else `milestones.title`. Every place in "What happens today" calls it; nothing else looks the card up.
- **D2 What a ticketless job does, in one line,** from its role: review "The lead reads what {key} built, before it's yours to sign off"; planner "The lead answers you on {key}'s thread"; checkpoint "Claude re-checks {key}'s merged tickets". One dict beside `job_card`; another role shows no line.
- **D3 The card's plate** is F132's project plate (`.proj`, f132-02, D3): mono, ink-2, a rule border, two corner ticks, no status colour; it links to `/planning/<key>`. The calmer variant in the mock-up is a plain mono link; the plate is proposed.
- **D4 After F132.** f132-02 reworks Now and Next in line, f132-06 the Jobs list: this card's ticket waits for both so neither is redone.
- **D5 Developer ticket.** `factory_dashboard/` is not protected; the ticket link in `running.html` and `running_jobs` are the example.

Picture: [`f62-mockup/now-names-the-card.html`](f62-mockup/now-names-the-card.html).

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | now-names-the-card | D | 3 | f132-02, f132-06 | D1–D3 on Now, the top bar, Next in line, Projects, Planning and Jobs |
