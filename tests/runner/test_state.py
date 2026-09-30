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


def test_numbered_milestones_from_an_older_state_file_become_keys(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(
        '{"headless_runs": {"4": 7}, "review_counts": {"3": [2, 1]}, "review_stop": {"3": "clean"}}'
    )
    state = load_state(path)
    assert state.runs_used("m4") == 7
    assert state.review_counts == {"m3": [2, 1]} and state.review_stop == {"m3": "clean"}
