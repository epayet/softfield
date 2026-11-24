# Review: F276, The top bar's dot and words see the lead's setup jobs

**Status:** round 1 done, ready for your sign-off. Score 7/10. Two should-fix points, both fixed by the review.

### 1. What changed
- While you have paused the factory and the lead sets up a new project, the top bar now lights the lead's dot and says "Paused by you since 11:40 · the lead is setting up wardrobe-teller".
- Not paused, it says "Running: the lead is setting up wardrobe-teller", and the pause button's words are "Pausing after the setup of wardrobe-teller".
- A planner job with no card reads "the lead is answering you", not "planner, job 2502". When the lead answers you and sets up a project at the same time, your conversation is what the bar shows.
- No setup job ran during the review, so the live page couldn't show the new words; the tests cover them.

### 2. How to test it yourself
1. Pause the factory, then start a new project from the Projects page.
2. While its setup runs, look at the top bar on your phone: the lead's dot is lit and the words name the project being set up.
3. Resume. While the setup still runs, the bar reads "Running: the lead is setting up …"; tap ⏸ and it reads "Pausing after the setup of …".
4. Paused, ask the lead something in the Planning room during a setup: the bar says "the lead is answering you".

### 3. Done when, as of now
- **Met:** paused with a live setup job, the bar reads "Paused by you since … · the lead is setting up X" with the lead's dot and Resume; with a planner job too, the planner's words win, now whatever the projects' order.
- **Met:** among paused projects, the one whose lead dot is lit is shown.
- **Met:** not paused, "Running: the lead is setting up X" with no project name repeated, and Pause says "Pausing after the setup of X".
- **Met:** not paused, a planner job with no card reads "the lead is answering you" ("Running: softfield · the lead is answering you" with several projects).
- **Met:** every earlier case of the top bar's test keeps its words and dot; the tests and gates pass.
- **Your check:** see it once on a real setup (no setup ran during the review).

### 5. Decisions made along the way
- **The owner's conversation wins over a setup across projects, not just within one.** The ticket's test only passed because the planner's project came first in the order; the review made the rank say so and added a case with the order reversed. *The review.*
- **The pause test posts to the sign's own project.** With two projects, the bar's ⏸ posts to the project it names, so the test now does the same rather than posting to the page's project. *Lead, on f276-01.*

### 8. How the work went
- The local model ran three attempts (about 3 h) without a green branch; the lead finished it in 15 minutes for $1.16, and added a developer note on `factory_wide_status` (a new winner is a step in `rank`, never a branch before `min`).
- The test fixture invented a setup job tidier than the runner's (no milestone); checking it against job 2525 caught it.

### 9. What clogged the factory line
- f276-01: about 3 h of local attempts (a timeout, then two failures) before the escalation. The top bar's rank is subtle cross-project logic; such tickets fit the lead better than a developer.

<!-- runner report -->
<!-- /runner report -->
