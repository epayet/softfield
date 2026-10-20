---
id: f142-03-phone-steps
milestone: f142-why-am-i-not-getting-notifications
difficulty: 2
depends_on: [f142-02-ntfy-sender]
files:
  - docs/notifications-on-the-phone.md
  - runner/setup.py
tests:
  - tests/runner/test_setup.py
---

### Goal
The owner has written steps to get the factory's notifications on their phone, and `softfield doctor` says whether notifications are set up.

### Context
Read `.factory/adr/31-notifications-to-a-closed-phone.md` (items 1, 4 and Cost and risk), then the notify module f142-02 added to `runner/` (the setting, `softfield notify setup` and `softfield notify test`) and `doctor` in `runner/setup.py`. Follow how `doctor` already reports each check, and its tests in `tests/runner/test_setup.py`.
- `docs/notifications-on-the-phone.md`, in plain numbered steps for an Android phone: on this machine run `softfield notify setup` once and note the topic; on the phone install "ntfy" from the Play Store, open it, tap +, type the topic, leave "Use another server" off, tap Subscribe, and allow notifications when Android asks; then run `softfield notify test` and see it arrive. Then: what a notification says and where a tap goes (ADR 31 item 1, the page opens only on the home Wi-Fi); turning off the dashboard's own notifications in Chrome on the phone so nothing comes twice; and what to do if the topic leaks (setup again with a new topic, which needs the old section removed first, and subscribe to the new one).
- `doctor` adds one check: notifications set up when `[notify] ntfy` is in the machine's settings file (`DEFAULT_MACHINE` in `runner/config.py`), else a line naming `softfield notify setup` and the doc. It sends nothing.

### Done when
- `docs/notifications-on-the-phone.md` has the steps above, numbered, with the command names exactly as `runner/cli.py` has them
- `doctor` with a `[notify] ntfy` setting reports notifications as set up, without a request leaving the machine
- `doctor` without one names `softfield notify setup` and `docs/notifications-on-the-phone.md`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
