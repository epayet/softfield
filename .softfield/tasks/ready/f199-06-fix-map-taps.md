---
id: f199-06-fix-map-taps
milestone: f199-let-s-improve-the-factory-floor
difficulty: 3
depends_on: []
files:
- factory_dashboard/static/factory.js
tests:
- tests/factory_dashboard/test_line.py
finding: f279-i-would-like-to-be-able-C2784-1
---

### Goal
Fix a checkpoint finding on f199-04-map-taps: Map taps only partially implement the ticket

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f199-04-map-taps.md`. What it found is under Finding:
- f279-i-would-like-to-be-able-C2784-1, blocking: in `factory_dashboard/static/factory.js`, line 1196.

### Finding
f279-i-would-like-to-be-able-C2784-1: Map taps only partially implement the ticket
> The Goal says a tap or Enter on each station, machine and belt opens a plain-word card linking to its destination. The implementation does not handle machines or belts: mapMachine/mapBelt are not marked as [data-what], and showMapCard only recognizes stations/planted/queue and falls through to machine lookup. It lacks belt handling entirely. Seeds also do not open their set-aside list or /board, sprouting has no /planning link, queue has an incorrect /queue link instead of /tickets and omits the first ten crates, ripe and harvested omit their required card lists/links, and machine cards omit the /agents link and keyboard/tab target markup. WHAT at the same station adds no tabindex or role, and short belt/machine targets do not guarantee the phone 44 px requirement. This breaks: “a tap or Enter on each station, machine and belt opens the card with its words; ... A belt’s card says its words, for instance 'your sign-off' and '7 went this way today'.”

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
