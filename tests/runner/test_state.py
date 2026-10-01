from runner.state import load_state, save_state


def test_round_trip(tmp_path):
    path = tmp_path / "runs" / "state.json"
    state = load_state(path)
    state.count_run("m1")
    state.count_run("m1")
    state.finding_seen["m1-F1"] = 2
    save_state(state, path)
    again = load_state(path)
    assert again.runs_used("m1") == 2 and again.runs_used("m2") == 0
    assert again.finding_seen == {"m1-F1": 2}


def test_the_in_flight_job_and_what_recovery_left_round_trip(tmp_path):
    """ADR 15 item 11: what the next run needs to recover a job a Ctrl-C cut off."""
    path = tmp_path / "state.json"
    state = load_state(path)
    assert state.in_flight is None and state.interrupted == {} and state.timed_out == {}
    state.in_flight = {"kind": "review", "ticket": None, "branch": "main", "job_id": 3}
    state.interrupted["review:f1-review-r1"] = {"session_id": "s1", "branch": "interrupted/x"}
    state.timed_out["f1-02-thing"] = 1
    save_state(state, path)
    again = load_state(path)
    assert again.in_flight == {"kind": "review", "ticket": None, "branch": "main", "job_id": 3}
    assert again.interrupted == {
        "review:f1-review-r1": {"session_id": "s1", "branch": "interrupted/x"}
    }
    assert again.timed_out == {"f1-02-thing": 1}


def test_numbered_milestones_from_an_older_state_file_become_keys(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(
        '{"headless_runs": {"4": 7}, "review_counts": {"3": [2, 1]}, "review_stop": {"3": "clean"}}'
    )
    state = load_state(path)
    assert state.runs_used("m4") == 7
    assert state.review_counts == {"m3": [2, 1]} and state.review_stop == {"m3": "clean"}
