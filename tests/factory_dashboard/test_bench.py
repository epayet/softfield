import re

from tests.factory_dashboard.conftest import LOCAL, OTHER_LOCAL


def text(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def rows(html: str) -> list[list[str]]:
    """Each body row of the grid: its cells' text. Columns: ticket, difficulty, then the
    agents in alphabetical order (``OTHER_LOCAL``, ``LOCAL``)."""
    body = re.search(r"<tbody>(.*?)</tbody>", html, re.S)
    assert body
    return [
        [text(cell) for cell in re.findall(r"<td.*?</td>", tr, re.S)]
        for tr in re.findall(r"<tr>.*?</tr>", body.group(1), re.S)
    ]


def test_two_tickets_by_two_agents_make_a_two_by_two_grid(bench_client):
    html = bench_client.get("/bench").text
    head = re.search(r"<thead>(.*?)</thead>", html, re.S)
    assert head
    assert text(head.group(1)) == f"Ticket Difficulty {OTHER_LOCAL} {LOCAL}"
    first, escalated = rows(html)
    assert first[:2] == ["f1-01-first", "4"]
    assert first[2] == "refused 10.0 min · 150k tokens"
    assert first[3] == "passed at attempt 2 20.0 min · 300k tokens"
    assert escalated[:2] == ["f1-02-escalated", "5"]
    assert escalated[3].startswith("would escalate")
    assert 'href="/tickets/f1-01-first?project=coucou"' in html


def test_a_pair_never_benched_is_an_empty_cell(bench_client):
    first, escalated = rows(bench_client.get("/bench").text)
    assert escalated[2] == ""
    assert first[2] != ""


def test_a_cell_links_to_the_last_bench_job(bench_client):
    html = bench_client.get("/bench").text
    assert re.search(r'href="/jobs/\d+\?project=coucou"[^>]*>\s*<span[^>]*>passed at', html)


def test_without_bench_jobs_the_page_explains_the_command(client):
    html = client.get("/bench").text
    assert "uv run runner bench &lt;ticket…&gt; --agents &lt;id…&gt;" in html
    assert "<tbody>" not in html
