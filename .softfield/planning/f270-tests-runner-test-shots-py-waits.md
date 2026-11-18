# F270: test_shots.py stops waiting on real seconds

The planning thread behind F270's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-18 19:13

> tests/runner/test_shots.py waits on the real page-readiness timeouts (12.5 s in test_a_slow_page_gets_its_pictures_and_no_readiness_request, about 5 s in three more): make those timeouts a parameter the tests set to a fraction of a second. From F71's review.

## The lead, 2026-11-18 19:16

> I've drafted F270's plan: one developer ticket, with no change to the runner's own code. The 12.5 s turned out to be the test's own sleep, not a runner limit.
>
> 1. **The 12.5 s is the test's own sleep, not a runner timeout**: test_a_slow_page_gets_its_pictures_and_no_readiness_request gives its tiny app a 6 s sleep on each page that exists, and two after pictures make 12 s. It was written to be 'slower than the old 5 s check', but that check is gone: the runner now only checks that the app's port is open. The test also uses the fake browser, which has no time limit, so the 6 s proves only that the fake waits. What still matters is that the app gets one request per picture and none for `/`. So the fix is a delay of a fraction of a second with the same checks, not a new timeout setting.
>    Action: In f270-01: the delay goes under half a second and the request check stays.
> 2. **Pushback: no new parameter in the runner**: You asked for the timeouts to become a parameter. They already can be set: the runner's limits are module values, and one test already sets the start-up limit to 0.5 s the same way. Passing a parameter through take, _round and _browse would change protected runner code only for the tests' sake. I recommend the tests set the existing values. Say so if you'd rather have the parameter anyway.
>    Action: Card decision D1: runner/shots.py is unchanged.
> 3. **The three '5 s' tests aren't named, so the ticket measures first**: F71's review didn't say which three tests take about 5 s. Most likely they are the tests in a real browser whose page never goes quiet: the one that submits a form, and the dashboard, which keeps polling. Each of those waits out the 5 s settle limit. Cutting that limit carries one risk: the busy page's test checks that requests made after load (`/redirect`, `/dark-theme`) were seen. The ticket keeps those checks, and each changed test must still fail when its behaviour is broken.
>    Action: f270-01 measures with --durations before and after, and each changed test must still fail on purpose.
> 4. **A developer builds it**: It is one test file, it follows an example already in that file, and nothing protected changes. The developer's ticket is marked tests-only, because a test speed-up can't fail on main's code. Two ready tickets also edit test_shots.py (F85's f85-08 and F260's f260-01), so whichever merges later may need a small rebase. That costs little.
>    Action: Nothing more.
>
> Proposals:
> - F270, test_shots.py stops waiting on real seconds (plan)
