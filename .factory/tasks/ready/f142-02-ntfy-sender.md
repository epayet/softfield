---
id: f142-02-ntfy-sender
milestone: f142-why-am-i-not-getting-notifications
agent: lead
difficulty: 4
depends_on: []
files:
  - runner/notify.py
  - runner/owner.py
  - runner/loop.py
  - runner/requests.py
  - runner/config.py
  - runner/cli.py
tests:
  - tests/runner/test_notify.py
---

### Goal
When the runner stores something that needs the owner, it sends one notification to ntfy.sh straight away, saying what kind of thing it is and opening the page where the owner acts.

### Context
Read `.factory/adr/31-notifications-to-a-closed-phone.md` (items 1–5: the words, the links, when it sends, nothing stored, the setting and the commands), then `upsert_owner_item` in `runner/metrics.py` and its three callers that store items: `_record_items` in `runner/owner.py`, `run_planner` in `runner/loop.py`, and the reserve switch going off in `runner/requests.py`. Follow `runner/local_model.py` for a web request with `urllib.request` and a timeout, and `_lan_address` in `runner/cli.py` for the dashboard's home address (port 8765, as `softfield dashboard --lan` serves it).
- A new module `runner/notify.py` sends: one POST to the setting's address, the words as the body, headers `Title` (the project's name) and `Click` (the dashboard's home address and the page's path with `?project=`). Nothing is stored about the sending: no table, no migration. The post never raises: a failure or the 5-second limit returns a short reason, which the caller adds to the run's report notes.
- An item sends when it is new or opens again (it was resolved). Read whether it is open before the upsert; leave `upsert_owner_item`'s return as it is. A lead's reply always sends.
- One verdict's items about one card are one notification (ADR 31 item 2).
- The setting is `[notify] ntfy` in the machine's settings file (`DEFAULT_MACHINE` in `runner/config.py`), never the project's. No setting: nothing is sent, nothing is reported.
- `softfield notify setup` writes the section with a topic of 24 random lowercase letters and digits (`secrets`) when it is missing, keeps the rest of the file as it is, and prints the topic; when the section is there it prints the topic it has. `softfield notify test` sends "softfield · Notifications work" and says whether ntfy.sh took it.
- Tests never reach the network: replace the request function, as `tests/runner/test_local_model.py` does.

### Done when
- a lead's reply on `f7` sends "<project> · The lead answered you", its `Click` ending `/planning/f7?project=<project>`
- an open item stored again (a verdict rerun) sends nothing; a resolved one opening again sends
- a verdict raising a sign-off and a stopped review on one card sends one notification, "<project> · 2 things need you on one card", opening that card's thread
- items of kind `adr`, `blocked` and `escalated` send "A ticket needs your decision"; the reserve switch going off sends "Claude's reserve: your choice"; all open the Overview
- no card title, reply text or stored item text is in any notification
- a request that fails or takes over 5 s adds one note to the run's report, and the job goes on
- with no `[notify]` section nothing is sent
- the metrics database's tables are the same before and after the change
- `softfield notify setup` writes the section once and keeps every other line of the file; run again, it prints the same topic
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
