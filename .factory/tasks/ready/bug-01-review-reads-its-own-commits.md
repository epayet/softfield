---
id: bug-01-review-reads-its-own-commits
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 3
finding: f104-mockups-act-like-i-can-interact-F2
files:
  - runner/milestone.py
  - docs/agents/lead.md
  - docs/backlog.md
tests:
  - tests/runner/test_milestone.py
---

### Goal
A milestone's round-1 review reads that milestone's commits, not everything committed since its card was planted or since its merge.

### Context
Read `def _plan_commit`, `def run_due_review`, `def _fix_scope` and the round-1 `scope` in `def review_milestone` in `runner/milestone.py`, and in `tests/runner/test_milestone.py` `test_a_replanned_milestones_review_diffs_from_its_first_merge` (the worked example) and `test_a_later_round_with_only_its_own_merges_reads_the_diff_since_the_last_round`.
- Twice on 2026-10-13:
  - F104: its one ticket, f104-01, was built in a terminal session, in a commit whose subject names it ("f109-02, f49-03, f104-01: …") with no `Task:` trailer. `_plan_commit` found no merge, fell back to the commit that added the card's doc (planted 2026-10-10), and round 1 was handed 158 files and 7,600 lines for a one-attribute change.
  - F79 (backlog, f79-F3): the tag was right, but a terminal session committed between the merge and the review, and 830 of the diff's 890 lines were other milestones'.
- The start: when no commit carries a `Task:` trailer for one of the milestone's done tickets, `_plan_commit` takes the parent of the earliest commit whose subject names one of them, by its id or its short id (`f104-01`), before falling back to the doc's commit.
- Round 1's scope: when commits in `base..main` are not the milestone's own (no `Task:` trailer of its tickets, no ticket of its named in the subject; the runner's own commits don't count), the prompt names the milestone's commits, one `git show <sha>` each, as `_fix_scope` does for later rounds, and says the others belong to other work. With only its own commits it stays `git diff base..main`.
- A commit that holds several tickets' work is still one commit: the prompt says which of its tickets are this milestone's.
- `docs/agents/lead.md`, where it speaks of the lead's own commits in a terminal session: a commit that builds a ticket names the ticket's id in its subject. One line.
- Remove the f79-F3 line from `docs/backlog.md`: this ticket replaces it.

### Done when
- a milestone whose only done ticket was committed with its id in the subject and no trailer, its doc added long before with other milestones' merges in between, gets its start tag on that commit's parent
- with a `Task:` merge present, the start is that merge's parent, as now (the existing test)
- round 1 with another milestone's merge in its range lists this milestone's commits by `git show` and holds no `git diff base..main`; with only its own it holds the diff, as now
- the runner's own commits ("runner: …") in the range don't change which of the two the prompt is
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
