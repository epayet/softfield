# Review: F272, The top bar says how long the job has run and which attempt it is

**Status:** round 1 done, ready for your sign-off. Score 8/10. One test gap, fixed by the review.

### 1. What changed
- On a wide screen (1200 px and up), a "Job" plate sits right after the bar's words: how long the job has run and, on a ticket, its attempt ("12 min · attempt 2 of 3", "attempt 3 of 3, the last" on the lead's last try).
- Narrower, the plate goes and hovering the words or the dot shows "Job running … · attempt …" under the sentence. On a phone, tapping the dot shows that line above "Computer on …".
- A planner, review, setup or checkpoint job shows the time only. The Overview's "Now" panel no longer says "attempt N" on those jobs.
- Matches the mock-up. The after pictures were taken between two jobs, so they show no plate. The live page read during this review shows "Job 0 min" on the review job and no attempt pill in Now.

### 2. How to test it yourself
1. While a developer ticket runs, open the Overview on a desktop wider than 1200 px: the "Job" plate after the words says e.g. "14 min · attempt 2 of 3" and moves on a minute later without a reload.
2. Narrow the window under 1200 px: the plate goes. Hover the words: the tooltip's second line is "Job running 14 min · attempt 2 of 3".
3. On the phone, tap the dot: the same line sits above "Computer on …".
4. While the lead answers you in the Planning room (paused or not), the plate shows the time alone, and "Now" shows no attempt pill on that job.

### 3. Done when, as of now
- **Met:** f272-01 is merged.
- **Your check:** the wide plate, the hover line under 1200 px and the phone's tapped line during a developer ticket (all three are covered by a browser test at 1280, 1000 and 390 px).
- **Met:** while the lead answers you, the plate shows the time alone, and "Now" doesn't say "attempt" on a planner (tested, and seen live on a review job).

### 5. Decisions made along the way
- **A setup job also shows its time, paused or running.** The words already name the setup as a live job, so D1's rule ("whenever the words name a live job") covers it. *Lead, on f272-01.*
- **The line is one `Status.job_line` property**, shared by the plate's title, the hover and the phone line, so the three can't drift apart. *Lead, on f272-01.*

### 6. What next
- **Product:** nothing new from this card. Product work stays on hold.
- **Factory:** a ticket that changes the top bar's markup and its browser tests belongs to the lead (F17's rule). f272-01 was planned as a developer ticket, and two of its three local attempts made no edit in 20 minutes. The planner should check the rule when it assigns a ticket.
  > When a planned ticket touches the top bar's markup or its browser tests in test_app.py, make the planner give it to the lead, as F17's rule says, rather than to a developer.

### 8. How the work went
- The local model read the same nine files twice without editing, then broke 17 tests with a Jinja `{% set %}` that printed instead of appending. The lead finished the branch, and `.softfield/developer.md` now has a worked example for the top bar (a `Status` property, what `{% set %}` does, the three test files that parse the bar).
- The tests are thorough: every role, every no-job state, two projects and a 1280/1000/390 px browser test. The review added the setup cases, the only path left untested.

### 9. What clogged the factory line
- f272-01: about 1 h of local attempts with nothing to merge (two stops after 20 min with no edit, then a timeout) before the lead finished it. The fix is the planning rule above.

<!-- runner report -->
<!-- /runner report -->
