"""Tests for the Agents page (/agents): efficiency, roles table, ratings."""

import json
import re
from pathlib import Path

from tests.factory_dashboard.conftest import LOCAL, OPUS, SONNET, SONNET_45, SONNET_46

CHARTS_JS = Path(__file__).parents[2] / "factory_dashboard" / "static" / "charts.js"
STATIC = Path(__file__).parents[2] / "factory_dashboard" / "static"
LAN = "http://192.168.1.20:8765"
DISPLAY = {"width": 1280, "height": 800}


def section(html: str, name: str) -> str:
    """The text of the page's ``<section id="name">``, tags stripped."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html, re.S)
    assert match, f"no section {name}"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())


def section_raw(html: str, name: str) -> str:
    """The raw HTML of the page's ``<section id="name">``."""
    match = re.search(rf'<section[^>]*\bid="{name}"[^>]*>(.*?)</section>', html, re.S)
    assert match, f"no section {name}"
    return match.group(1)


def charts(html: str) -> dict[str, object]:
    """Each chart's kind and its JSON data block (f1 D5)."""
    found = re.findall(
        r'<div[^>]*data-chart="([a-z-]+)"[^>]*></div>\s*'
        r'<script type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    return {kind: json.loads(data) for kind, data in found}


def test_efficiency_numbers_for_fixture_local_agent(serve):
    html = serve(live=False).get("/agents").text
    eff = section(html, "efficiency")
    assert LOCAL in eff
    # Read the local agent's row cell by cell (raw HTML)
    eff_raw = section_raw(html, "efficiency")
    local_row_match = re.search(rf"<tr>.*?{re.escape(LOCAL)}.*?</tr>", eff_raw, re.S)
    assert local_row_match, f"no row for {LOCAL}"
    local_row = local_row_match.group(0)
    # jobs=5
    assert '<td class="num">5</td>' in local_row
    # merged=2
    assert '<td class="num">2</td>' in local_row
    # attempt_tickets=3
    assert '<td class="num">3</td>' in local_row
    # first_attempt_pass=67%
    assert "67%" in local_row
    # attempts_per_merge=2.5
    assert '<td class="num">2.5</td>' in local_row
    # minutes_per_merge=25.0
    assert '<td class="num">25.0</td>' in local_row
    # tokens_per_merge=287500
    assert '<td class="num">287500</td>' in local_row
    # tokens_per_second=192
    assert '<td class="num">192</td>' in local_row
    # escalation_rate=33%
    assert "33%" in local_row
    # dollars=$0.00
    assert "$0.00" in local_row
    # most_failed_gate=–
    assert "\u2013" in local_row


def test_agents_roles_table_has_cell_per_pair(client):
    html = client.get("/agents").text
    roles = section(html, "roles")
    assert LOCAL in roles
    assert OPUS in roles
    assert SONNET in roles
    assert "developer" in roles
    assert "checkpoint" in roles
    assert "review" in roles


def test_empty_state_when_no_ratings(serve):
    html = serve(live=False).get("/agents").text
    ratings = section(html, "ratings")
    assert "Ratings start after f1-24" in ratings
    assert "data-chart" not in ratings


def test_rating_chart_json_with_two_changes(rating_client):
    html = rating_client.get("/agents").text
    c = charts(html)
    assert "rating" in c
    data = c["rating"]
    assert len(data["labels"]) == 2  # type: ignore[index]
    assert len(data["agents"]) == 2  # type: ignore[index]
    assert len(data["skills"]) == 2  # type: ignore[index]
    assert len(data["scores"]) == 2  # type: ignore[index]
    assert data["agents"][0] == LOCAL  # type: ignore[index]
    assert data["skills"][0] == "coding"  # type: ignore[index]
    assert data["scores"][0] == 4.5  # type: ignore[index]


def test_claude_sonnet_shows_dashes_for_per_merge(serve):
    html = serve(live=False).get("/agents").text
    eff = section(html, "efficiency")
    assert SONNET in eff
    # Find the row containing SONNET (raw HTML)
    eff_raw = section_raw(html, "efficiency")
    sonnet_row_match = re.search(rf"<tr>.*?{re.escape(SONNET)}.*?</tr>", eff_raw, re.S)
    assert sonnet_row_match, f"no row for {SONNET}"
    sonnet_row = sonnet_row_match.group(0)
    # jobs=1
    assert '<td class="num">1</td>' in sonnet_row
    # merged=0, so per-merge values are dashes
    assert "\u2013" in sonnet_row


def test_milestone_filter_filters_every_query(serve):
    """``/agents?milestone=f1`` answers 200; m4-01-old drops from the local row."""
    resp = serve(live=False).get("/agents?milestone=f1")
    assert resp.status_code == 200
    html = resp.text
    eff = section(html, "efficiency")
    assert LOCAL in eff
    # Find the local agent's row (raw HTML)
    eff_raw = section_raw(html, "efficiency")
    local_row_match = re.search(rf"<tr>.*?{re.escape(LOCAL)}.*?</tr>", eff_raw, re.S)
    assert local_row_match, f"no row for {LOCAL}"
    local_row = local_row_match.group(0)
    # m4-01-old job drops out: jobs=4 (was 5), merged=1 (was 2)
    assert '<td class="num">4</td>' in local_row
    assert '<td class="num">1</td>' in local_row


def efficiency_rows(html: str) -> list[list[str]]:
    """The efficiency table's rows, each a list of its cells' text."""
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", section_raw(html, "efficiency"), re.S)
    cells = [re.findall(r"<td[^>]*>(.*?)</td>", row, re.S) for row in rows]
    return [[" ".join(re.sub(r"<[^>]+>|&nbsp;|↳", " ", c).split()) for c in r] for r in cells if r]


def test_a_ticket_merged_after_three_attempts_is_one_merge(serve, db_path):
    """f2 review: `merged` counted the jobs on merged tickets, so three attempts at one ticket
    read as three merges and 1.0 attempts per merge."""
    from runner import metrics
    from tests.factory_dashboard.conftest import PROJECT, _job

    client = serve(live=False)
    agent = "ollama-gpt-oss-120b"
    conn = metrics.open_db(db_path)
    try:
        project = metrics.upsert_project(conn, PROJECT)
        f2 = metrics.upsert_milestone(conn, project, "f2")
        run = metrics.upsert_run(conn, project, "20261002-120000", command="milestone f2")
        ticket = metrics.upsert_ticket(
            conn, project, "f2-06-x", milestone_id=f2, kind="developer", merged_by=agent
        )
        for attempt, outcome in ((1, "failed"), (2, "failed"), (3, "passed")):
            _job(conn, run, f2, ticket, "developer", agent, attempt, outcome)
    finally:
        conn.close()
    [row] = [r for r in efficiency_rows(client.get("/agents").text) if r[0] == agent]
    # jobs, merged, tickets attempted, first-attempt pass, attempts per merge
    assert row[1:6] == ["3", "1", "1", "0%", "3.0"]


def test_agent_on_two_models_gets_a_row_per_model(models_client):
    """f2-07: claude-sonnet's own row totals its 5 jobs, then one row per model; NULL and ''
    are one "not recorded" group."""
    rows = efficiency_rows(models_client.get("/agents").text)
    names = [r[0] for r in rows]
    at = names.index(SONNET)
    sonnet = {r[0]: (r[1], r[-1]) for r in rows[at : at + 4]}
    assert sonnet == {
        SONNET: ("5", "$1.80"),
        "before 2 Oct (model not recorded)": ("2", "$0.50"),
        SONNET_45: ("1", "$0.50"),
        SONNET_46: ("2", "$0.80"),
    }


def test_agent_on_one_model_gets_no_model_rows(models_client):
    """Only claude-sonnet's three model rows appear, none for the local agent or Opus."""
    eff = section_raw(models_client.get("/agents").text, "efficiency")
    assert eff.count('<tr class="model">') == 3


def test_default_fixture_has_no_model_rows(serve):
    eff = section_raw(serve(live=False).get("/agents").text, "efficiency")
    assert '<tr class="model">' not in eff


def test_rating_chart_has_one_series_per_agent(rating_client):
    """The rating chart has one series per agent, named by the agent."""
    html = rating_client.get("/agents").text
    c = charts(html)
    assert "rating" in c
    data = c["rating"]
    # Both points present
    assert len(data["scores"]) == 2  # type: ignore[index]
    # One series per agent (the JS draws one series per unique agent)
    unique_agents = len(set(data["agents"]))  # type: ignore[index]
    assert unique_agents == 1
    assert LOCAL in data["agents"]  # type: ignore[index]


def test_work_kind_returns_pages_when_any_page_file():
    from factory_dashboard.agents import work_kind

    assert work_kind(["a.html"]) == "Pages"
    assert work_kind(["a.css"]) == "Pages"
    assert work_kind(["a.js"]) == "Pages"
    assert work_kind(["a.py", "b.html"]) == "Pages"
    assert work_kind(["templates/x.html", "a.py"]) == "Pages"


def test_work_kind_returns_code_no_pages_when_no_page_files():
    from factory_dashboard.agents import work_kind

    assert work_kind(["a.py"]) == "Code, no pages"
    assert work_kind(["a.md"]) == "Code, no pages"
    assert work_kind(["a.py", "b.md"]) == "Code, no pages"


def test_work_kind_returns_code_no_pages_when_none():
    from factory_dashboard.agents import work_kind

    assert work_kind(None) == "Code, no pages"
    assert work_kind([]) == "Code, no pages"


def test_by_kind_bay_section_exists_on_page(serve):
    """The by-kind bay section appears on the Agents page."""
    html = serve(live=False).get("/agents").text
    assert 'id="by-kind"' in html


def test_by_kind_data_with_merged_first_attempt_is_one(serve, db_path):
    """A ticket merged at the first attempt scores 1.0."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    ticket = metrics.upsert_ticket(
        conn,
        project,
        "f1-99-pages",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        files=["a.html", "b.py"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        5.0,
        5.5,
        at="2026-09-30T12:00:00+02:00",
        ticket_id=ticket,
        result="merged at the first attempt",
    )
    data = by_kind_data(conn, "coucou")
    rows = data["rows"]
    assert len(rows) == 1
    assert rows[0]["tickets"] == 1
    assert rows[0]["score"] == 100  # 1.0 * 100
    assert rows[0]["few"] is True
    conn.close()


def test_by_kind_data_merged_later_scores_half(serve, db_path):
    """Merged later scores 0.5."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    ticket = metrics.upsert_ticket(
        conn,
        project,
        "f1-98-code",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        files=["a.py"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        5.0,
        5.5,
        at="2026-09-30T12:00:00+02:00",
        ticket_id=ticket,
        result="merged later",
    )
    data = by_kind_data(conn, "coucou")
    rows = data["rows"]
    assert len(rows) == 1
    assert rows[0]["score"] == 50  # 0.5 * 100
    conn.close()


def test_by_kind_data_not_merged_scores_zero(serve, db_path):
    """Not merged scores 0."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    ticket = metrics.upsert_ticket(
        conn,
        project,
        "f1-97-not",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        files=["a.py"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        5.0,
        4.5,
        at="2026-09-30T12:00:00+02:00",
        ticket_id=ticket,
        result="not merged",
    )
    data = by_kind_data(conn, "coucou")
    rows = data["rows"]
    assert len(rows) == 1
    assert rows[0]["score"] == 0
    conn.close()


def test_by_kind_data_excludes_bench_games(serve, db_path):
    """Bench games (result starting 'bench ') are not counted."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    ticket = metrics.upsert_ticket(
        conn,
        project,
        "f1-96-bench",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        files=["a.py"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        5.0,
        5.5,
        at="2026-09-30T12:00:00+02:00",
        ticket_id=ticket,
        result="bench passed at the first attempt",
    )
    data = by_kind_data(conn, "coucou")
    rows = data["rows"]
    assert len(rows) == 0
    conn.close()


def test_by_kind_data_excludes_finding_penalties(serve, db_path):
    """Finding penalties (result starting 'finding ') are not counted."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    ticket = metrics.upsert_ticket(
        conn,
        project,
        "f1-95-finding",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        files=["a.py"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        5.0,
        4.75,
        at="2026-09-30T12:00:00+02:00",
        ticket_id=ticket,
        result="finding F1",
    )
    data = by_kind_data(conn, "coucou")
    rows = data["rows"]
    assert len(rows) == 0
    conn.close()


def test_by_kind_gap_words_better_when_above_plus_5(serve, db_path):
    """Gap above +5 reads 'better'."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    # Need 3+ tickets to avoid "too few to say"
    for i in range(3):
        ticket = metrics.upsert_ticket(
            conn,
            project,
            f"f1-94-good-{i}",
            milestone_id=f1,
            kind="developer",
            state="done",
            difficulty=3,
            files=["a.html"],
        )
        metrics.add_rating_change(
            conn,
            LOCAL,
            "coding",
            3.0,
            3.5,
            at=f"2026-09-30T{12 + i}:00:00+02:00",
            ticket_id=ticket,
            result="merged at the first attempt",
        )
    data = by_kind_data(conn, "coucou")
    rows = data["rows"]
    assert len(rows) == 1
    # Score=100, expected≈50, gap≈50 → "better"
    assert rows[0]["gap_words"] == "better"
    conn.close()


def test_by_kind_gap_words_worse_when_below_minus_5(serve, db_path):
    """Gap below −5 reads 'worse'."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    # Need 3+ tickets to avoid "too few to say"
    for i in range(3):
        ticket = metrics.upsert_ticket(
            conn,
            project,
            f"f1-93-bad-{i}",
            milestone_id=f1,
            kind="developer",
            state="done",
            difficulty=7,
            files=["a.py"],
        )
        # Rating 7, difficulty 7 → expected ≈ 0.5, result 0 → gap ≈ −0.5 = −50 points
        metrics.add_rating_change(
            conn,
            LOCAL,
            "coding",
            7.0,
            6.5,
            at=f"2026-09-30T{12 + i}:00:00+02:00",
            ticket_id=ticket,
            result="not merged",
        )
    data = by_kind_data(conn, "coucou")
    rows = data["rows"]
    assert len(rows) == 1
    assert rows[0]["gap_words"] == "worse"
    conn.close()


def test_by_kind_gap_words_as_rated_when_within_5(serve, db_path):
    """Gap within ±5 reads 'as rated'."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    # Need 3+ tickets to avoid "too few to say"
    for i in range(3):
        ticket = metrics.upsert_ticket(
            conn,
            project,
            f"f1-92-rated-{i}",
            milestone_id=f1,
            kind="developer",
            state="done",
            difficulty=5,
            files=["a.py"],
        )
        # Rating 5, difficulty 5 → expected ≈ 0.5, result 0.5 → gap ≈ 0
        metrics.add_rating_change(
            conn,
            LOCAL,
            "coding",
            5.0,
            5.5,
            at=f"2026-09-30T{12 + i}:00:00+02:00",
            ticket_id=ticket,
            result="merged later",
        )
    data = by_kind_data(conn, "coucou")
    rows = data["rows"]
    assert len(rows) == 1
    assert rows[0]["gap_words"] == "as rated"
    conn.close()


def test_by_kind_gap_words_too_few_when_under_3_tickets(serve, db_path):
    """Fewer than 3 tickets says 'too few to say'."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    ticket = metrics.upsert_ticket(
        conn,
        project,
        "f1-91-few",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=3,
        files=["a.html"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        3.0,
        3.5,
        at="2026-09-30T12:00:00+02:00",
        ticket_id=ticket,
        result="merged at the first attempt",
    )
    data = by_kind_data(conn, "coucou")
    rows = data["rows"]
    assert len(rows) == 1
    assert rows[0]["few"] is True
    assert rows[0]["gap_words"] == "too few to say"
    conn.close()


def test_by_kind_milestone_filter_limits_bay(serve, db_path):
    """The milestone filter limits the bay like it limits Ratings."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    m4 = metrics.upsert_milestone(conn, project, "m4")
    # Ticket in f1
    ticket_f1 = metrics.upsert_ticket(
        conn,
        project,
        "f1-90-f1",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        files=["a.html"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        4.0,
        4.5,
        at="2026-09-30T12:00:00+02:00",
        ticket_id=ticket_f1,
        result="merged at the first attempt",
    )
    # Ticket in m4
    ticket_m4 = metrics.upsert_ticket(
        conn,
        project,
        "m4-99-m4",
        milestone_id=m4,
        kind="developer",
        state="done",
        difficulty=2,
        files=["b.py"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        4.0,
        4.5,
        at="2026-09-20T12:00:00+02:00",
        ticket_id=ticket_m4,
        result="merged at the first attempt",
    )
    # With milestone=f1, only the f1 ticket should appear
    data_f1 = by_kind_data(conn, "coucou", milestone="f1")
    f1_rows = [r for r in data_f1["rows"] if r["agent"] == LOCAL]
    assert len(f1_rows) == 1
    assert f1_rows[0]["tickets"] == 1
    # With no milestone, both should appear
    data_all = by_kind_data(conn, "coucou")
    all_rows = [r for r in data_all["rows"] if r["agent"] == LOCAL]
    assert len(all_rows) == 2
    conn.close()


def test_by_kind_no_coding_games_says_so(serve):
    """With no coding games the bay says so."""
    html = serve(live=False).get("/agents").text
    assert "No coding games to show" in html


def test_by_kind_separates_pages_and_code(serve, db_path):
    """Pages and Code, no pages are separate rows for the same agent."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    # Pages ticket
    ticket_pages = metrics.upsert_ticket(
        conn,
        project,
        "f1-89-pages",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        files=["a.html"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        4.0,
        4.5,
        at="2026-09-30T12:00:00+02:00",
        ticket_id=ticket_pages,
        result="merged at the first attempt",
    )
    # Code ticket
    ticket_code = metrics.upsert_ticket(
        conn,
        project,
        "f1-88-code",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=4,
        files=["b.py"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        4.0,
        4.5,
        at="2026-09-30T13:00:00+02:00",
        ticket_id=ticket_code,
        result="merged at the first attempt",
    )
    data = by_kind_data(conn, "coucou")
    rows = [r for r in data["rows"] if r["agent"] == LOCAL]
    kinds = {r["kind"] for r in rows}
    assert "Pages" in kinds
    assert "Code, no pages" in kinds
    conn.close()


def test_by_kind_expected_uses_difficulty_corrected_when_set(serve, db_path):
    """Expected uses difficulty_corrected when set, else difficulty."""
    from factory_dashboard.agents import by_kind_data
    from runner import metrics
    from runner.ratings import expected as rating_expected

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    # Ticket with difficulty_corrected
    ticket_corrected = metrics.upsert_ticket(
        conn,
        project,
        "f1-87-corrected",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=5,
        difficulty_corrected=3,
        files=["a.py"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        4.0,
        4.5,
        at="2026-09-30T12:00:00+02:00",
        ticket_id=ticket_corrected,
        result="merged at the first attempt",
    )
    # Ticket without difficulty_corrected
    ticket_no_corrected = metrics.upsert_ticket(
        conn,
        project,
        "f1-86-no-corrected",
        milestone_id=f1,
        kind="developer",
        state="done",
        difficulty=6,
        files=["b.py"],
    )
    metrics.add_rating_change(
        conn,
        LOCAL,
        "coding",
        4.0,
        4.5,
        at="2026-09-30T13:00:00+02:00",
        ticket_id=ticket_no_corrected,
        result="merged at the first attempt",
    )
    data = by_kind_data(conn, "coucou")
    rows = [r for r in data["rows"] if r["agent"] == LOCAL]
    assert len(rows) == 1
    # Both tickets are Code, no pages, so their expected is averaged
    # difficulty_corrected=3 for first, difficulty=6 for second
    exp1 = rating_expected(4.0, 3)
    exp2 = rating_expected(4.0, 6)
    expected_avg = round((exp1 + exp2) / 2 * 100)
    assert data["rows"][0]["expected"] == expected_avg
    conn.close()


def _seed_page_games(db_path, games, files=("factory_dashboard/templates/x.html",)):
    """Coding games of LOCAL on page tickets: ``(result, before, difficulty)`` each."""
    from runner import metrics

    conn = metrics.open_db(db_path)
    project = metrics.upsert_project(conn, "coucou")
    f1 = metrics.upsert_milestone(conn, project, "f1")
    for i, (result, before, difficulty) in enumerate(games):
        ticket = metrics.upsert_ticket(
            conn,
            project,
            f"f80-9{i}-page",
            milestone_id=f1,
            kind="developer",
            state="done",
            difficulty=difficulty,
            files=list(files),
        )
        metrics.add_rating_change(
            conn,
            LOCAL,
            "coding",
            before,
            before,
            at=f"2026-09-30T1{i}:00:00+02:00",
            ticket_id=ticket,
            result=result,
        )
    return conn


def test_by_kind_pages_row_averages_three_games(db_path):
    """Merged first (1), merged later (0.5) and not merged (0): 3 tickets, 50%, and expected the
    average of each game's own ``expected(before, difficulty)``."""
    from factory_dashboard.agents import by_kind_data
    from runner.ratings import expected

    games = [
        ("merged at the first attempt", 4.0, 3),
        ("merged later", 5.0, 6),
        ("not merged", 3.0, 4),
    ]
    conn = _seed_page_games(db_path, games)
    (row,) = by_kind_data(conn, "coucou")["rows"]
    conn.close()
    assert (row["kind"], row["tickets"], row["score"]) == ("Pages", 3, 50)
    assert row["expected"] == round(100 * sum(expected(b, d) for _, b, d in games) / 3)
    assert row["few"] is False


def test_by_kind_skips_a_game_whose_ticket_has_no_difficulty(db_path):
    from factory_dashboard.agents import by_kind_data

    conn = _seed_page_games(
        db_path, [("merged at the first attempt", 4.0, 3), ("not merged", 4.0, None)]
    )
    (row,) = by_kind_data(conn, "coucou")["rows"]
    conn.close()
    assert (row["tickets"], row["score"]) == (1, 100)


def test_by_kind_bay_shows_each_row_on_the_page(serve, db_path):
    """The page draws the row's agent, kind, count, score and words, not the empty line."""
    conn = _seed_page_games(db_path, [("merged at the first attempt", 3.0, 3)] * 3)
    conn.close()
    html = serve(live=False).get("/agents").text
    bay = section(html, "by-kind")
    assert f"{LOCAL} Pages 3 100% 50% +50 better" in bay
    assert "No coding games to show" not in bay
    assert "var(--qwen)" in section_raw(html, "by-kind")


def test_by_kind_as_rated_gap_carries_its_sign(serve, db_path):
    """A gap within 5 points is signed like "+50 better": score 50, expected 46, "+4 as rated"."""
    conn = _seed_page_games(db_path, [("merged later", 2.7, 3)] * 3)
    conn.close()
    bay = section(serve(live=False).get("/agents").text, "by-kind")
    assert f"{LOCAL} Pages 3 50% 46% +4 as rated" in bay


def test_an_agents_next_version_keeps_its_familys_colour():
    from factory_dashboard.agents import _agent_token

    assert _agent_token("local-qwen3.7-35b-a3b") == "--qwen"
    assert _agent_token("ollama-nemotron-3-ultra") == "--nemo"
    assert _agent_token("claude-opus") == "--opus"
    assert _agent_token("ollama-gemma4-31b") == "--muted"


def test_lead_panel_shows_with_non_opus_lead_ticket(lead_client):
    """With Sonnet and Opus lead tickets, the panel shows the saving, two bars and a table row."""
    html = lead_client.get("/agents").text
    # Panel section exists
    assert 'id="lead"' in html
    panel = section(html, "lead")
    # Readout shows total saved
    assert "saved" in panel
    # Two bars present
    assert "Opus would have" in panel
    assert "Sonnet" in panel
    # Table rows per agent-band
    table_raw = section_raw(html, "lead")
    assert "claude-sonnet" in table_raw
    assert "claude-opus" in table_raw
    # Difficulty band for Sonnet (d4 → "difficulty 4 or below")
    assert "difficulty 4 or below" in panel
    # Opus d5 → "difficulty 5 and up"
    assert "difficulty 5 and up" in panel


def test_lead_panel_absent_without_non_opus_lead_ticket(serve):
    """With no non-Opus lead ticket there is no panel."""
    html = serve(live=False).get("/agents").text
    assert 'id="lead"' not in html


def test_lead_panel_sonnet_totals_exclude_opus_rows(lead_client):
    """f179-07: Sonnet totals must not include Opus-owned tickets."""
    html = lead_client.get("/agents").text
    lead_raw = section_raw(html, "lead")
    # The panel section must have the 'lead' class for CSS to apply
    assert re.search(r'<section[^>]*\bid="lead"[^>]*class="[^"]*lead[^"]*"', html)
    # Sonnet bar width reflects only non-Opus dollars vs non-Opus would-have
    # Sonnet row: would_have=$3.00 (Opus mean at d4), dollars=$0.50 → 17%
    assert re.search(r"width:17%", lead_raw)
    # Total saved is only from non-Opus rows: $2.50
    assert "$2.50" in section(html, "lead")


def test_who_did_what_has_lead_ticket_and_planner_columns(client):
    """D5: "Who did what" has lead-ticket and planner columns, in D5's order."""
    html = client.get("/agents").text
    # Extract column headers from raw HTML
    roles_raw = section_raw(html, "roles")
    headers = re.findall(r"<th[^>]*>([^<]+)</th>", roles_raw)
    # D5 order: developer, last-attempt, lead-ticket, direction, escalation,
    # checkpoint, review, planner
    expected_order = [
        "developer",
        "last-attempt",
        "lead-ticket",
        "direction",
        "escalation",
        "checkpoint",
        "review",
        "planner",
    ]
    for _i, col in enumerate(expected_order):
        assert col in headers, f"missing column {col}; got {headers}"
    # Verify order: each expected column appears after the previous one
    last_idx = -1
    for col in expected_order:
        idx = headers.index(col)
        assert idx > last_idx, (
            f"{col} appears before {expected_order[expected_order.index(col) - 1]}"
        )
        last_idx = idx


def test_lead_bars_scale_to_their_inline_width(page, lead_client):
    """The Sonnet and Opus fills show at their inline widths, the ratio is about 0.17."""

    def route(r) -> None:
        url = r.request.url.removeprefix(LAN)
        path = url.split("?", 1)[0]
        if path.startswith("/static/"):
            r.fulfill(path=str(STATIC / path.removeprefix("/static/")))
        else:
            r.fulfill(body=lead_client.get(url).text, content_type="text/html; charset=utf-8")

    page.set_viewport_size(DISPLAY)
    page.route(f"{LAN}/**", route)
    page.goto(LAN + "/agents")
    sonnet_fill = page.locator(".bar.sonnet .fill")
    opus_fill = page.locator(".bar.opus .fill")
    sonnet_fill.wait_for(state="visible", timeout=5000)
    opus_fill.wait_for(state="visible", timeout=5000)
    sonnet_w = sonnet_fill.bounding_box()["width"]
    opus_w = opus_fill.bounding_box()["width"]
    assert sonnet_w > 0 and opus_w > 0
    ratio = sonnet_w / opus_w
    assert 0.15 <= ratio <= 0.19, f"ratio {ratio:.3f} not about 0.17"
    assert sonnet_fill.is_visible()
    assert opus_fill.is_visible()
    sonnet_label = page.locator(".bar.sonnet .label")
    opus_label = page.locator(".bar.opus .label")
    sonnet_label.wait_for(state="visible", timeout=5000)
    opus_label.wait_for(state="visible", timeout=5000)
    assert sonnet_label.is_visible()
    assert opus_label.is_visible()
