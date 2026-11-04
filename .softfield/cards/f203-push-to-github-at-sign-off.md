# Milestone F203: A sign-off pushes the milestone to GitHub

> **State:** done · **Priority:** 0 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-04. Base: git tag `f203-push-to-github-at-sign-off-start`. Report: [`.softfield/reviews/f203-push-to-github-at-sign-off.md`](../reviews/f203-push-to-github-at-sign-off.md).
> From the owner's terminal session of 2026-11-02.

## Notes
I want to push to my GitHub soon: scan if there's anything that shouldn't be committed, and let's discuss pushing to GitHub at the end of milestones deterministically.

## Done (2026-11-02, terminal session)
[ADR 42](../adr/42-sign-off-pushes-to-github.md), accepted by the owner. History rewritten first: the old work address is gone from every branch and tag, the trees byte-identical. Scanned: all of main's history for keys, tokens, risky files and the notification topic, clean. Softfield is MIT. The repo is public, as the owner chose.

The owner made the first push by hand on 2026-11-02 (main at `78aaa8ec`), and asked that a project pushes whenever its origin is set, with no other setting. The runner takes it from there.
