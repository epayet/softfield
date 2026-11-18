# Milestone F270: tests/runner/test_shots.py waits on the real…

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-18.

## Notes
tests/runner/test_shots.py waits on the real page-readiness timeouts (12.5 s in test_a_slow_page_gets_its_pictures_and_no_readiness_request, about 5 s in three more): make those timeouts a parameter the tests set to a fraction of a second. From F71's review.
