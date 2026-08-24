from datetime import datetime

from monitor.models import Mention
from monitor.report_html import render_html


def make_mention(title="Uppsalahem bygger nytt", url="https://example.com/1", **kwargs):
    return Mention(source="google_news", category="redaktionellt", title=title, url=url, **kwargs)


def test_render_html_shows_new_mentions_grouped_by_category():
    new = [
        make_mention(title="Uppsalahem bygger nytt", url="https://example.com/1"),
        Mention(source="reddit", category="socialt", title="Bra hyresvärd", url="https://example.com/2"),
    ]
    html_out = render_html(new, [m.to_dict() for m in new], datetime(2026, 8, 24, 14, 32))

    assert "2 ny(a) nämning(ar)" in html_out
    assert "Redaktionellt" in html_out
    assert "Socialt" in html_out
    assert "Uppsalahem bygger nytt" in html_out
    assert "Bra hyresvärd" in html_out
    assert "24 augusti 2026, 14:32" in html_out


def test_render_html_empty_state_when_no_new_mentions():
    html_out = render_html([], [], datetime(2026, 8, 24, 9, 0))
    assert "Inga nya nämningar sedan förra kontrollen" in html_out
    assert "Inga nämningar hittade ännu." in html_out


def test_render_html_escapes_content():
    dangerous = make_mention(title="<script>alert(1)</script>", url="https://example.com/xss")
    html_out = render_html([dangerous], [dangerous.to_dict()], datetime(2026, 8, 24, 9, 0))

    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;" in html_out


def test_render_html_marks_history_items_seen_before_as_not_new():
    new = [make_mention(title="Ny artikel", url="https://example.com/new")]
    old_entry = make_mention(title="Gammal artikel", url="https://example.com/old").to_dict()
    old_entry["checked_at"] = "2020-01-01T00:00:00+00:00"

    # I verkligheten skickas hela loggen (inklusive de nyss tillagda nya
    # posterna) in som `all_entries`, precis som main.py gör.
    html_out = render_html(new, [*[m.to_dict() for m in new], old_entry], datetime(2026, 8, 24, 9, 0))

    # Den nya träffen får en NY-badge både i "nya sedan sist"-panelen och
    # i historiklistan; den gamla ska aldrig ha en.
    assert html_out.count('<span class="badge">NY</span>') == 2
    assert "Gammal artikel" in html_out
