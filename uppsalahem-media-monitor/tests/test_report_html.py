from datetime import datetime, timezone

from monitor.models import Mention
from monitor.report_html import _parse_any_datetime, render_html


def make_mention(title="Uppsalahem bygger nytt", url="https://example.com/1", **kwargs):
    return Mention(source="google_news", category="redaktionellt", title=title, url=url, **kwargs)


def test_render_html_shows_new_mentions_grouped_by_category():
    new = [
        make_mention(title="Uppsalahem bygger nytt", url="https://example.com/1"),
        Mention(source="reddit", category="socialt", title="Bra hyresvärd", url="https://example.com/2"),
    ]
    html_out = render_html(new, [m.to_dict() for m in new], datetime(2026, 8, 24, 14, 32))

    assert '>2</span> ny(a) nämning(ar)' in html_out
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


def test_render_html_sorts_history_by_publish_date_not_discovery_order():
    # "old_news" hittades sist av verktyget (senast i loggen) men handlar om
    # en äldre nyhet; "recent_news" hittades tidigare men är en färskare
    # nyhet. Rapporten ska visa den färskaste nyheten först.
    old_news = make_mention(title="Gammal nyhet", url="https://example.com/old",
                             published_at="Mon, 01 Jan 2024 08:00:00 GMT").to_dict()
    old_news["checked_at"] = "2026-08-24T10:00:00+00:00"

    recent_news = make_mention(title="Färsk nyhet", url="https://example.com/recent",
                                published_at="Mon, 24 Aug 2026 08:00:00 GMT").to_dict()
    recent_news["checked_at"] = "2026-08-20T10:00:00+00:00"

    html_out = render_html([], [old_news, recent_news], datetime(2026, 8, 24, 12, 0))

    assert html_out.index("Färsk nyhet") < html_out.index("Gammal nyhet")


def test_render_html_falls_back_to_checked_at_when_published_at_missing():
    no_date = make_mention(title="Utan datum", url="https://example.com/no-date", published_at="").to_dict()
    no_date["checked_at"] = "2026-08-24T10:00:00+00:00"

    with_date = make_mention(title="Med datum", url="https://example.com/with-date",
                              published_at="Mon, 01 Jan 2020 08:00:00 GMT").to_dict()
    with_date["checked_at"] = "2020-01-01T10:00:00+00:00"

    # Utan tolkningsbart publiceringsdatum faller den tillbaka på
    # checked_at, som här är nyare än "with_date"s faktiska publiceringsdatum.
    html_out = render_html([], [with_date, no_date], datetime(2026, 8, 24, 12, 0))

    assert html_out.index("Utan datum") < html_out.index("Med datum")


def test_render_html_includes_data_attributes_for_filtering_and_read_tracking():
    m = make_mention(title="Uppsalahem-nyhet", url="https://example.com/1")
    html_out = render_html([m], [m.to_dict()], datetime(2026, 8, 24, 9, 0))

    assert f'data-id="{m.id}"' in html_out
    assert 'data-source="google_news"' in html_out


def test_render_html_same_mention_shares_id_across_new_and_history_panels():
    # En träff som är ny finns med både i "nya sedan sist"-panelen och i
    # historiklistan – de måste dela data-id så att klientens JS kan
    # markera båda kopiorna som lästa när användaren klickar på endera.
    m = make_mention(title="Uppsalahem-nyhet", url="https://example.com/1")
    html_out = render_html([m], [m.to_dict()], datetime(2026, 8, 24, 9, 0))

    assert html_out.count(f'data-id="{m.id}"') == 2


def test_render_html_script_marks_all_matching_ids_as_read():
    # Skydd mot regression: klientens markRead() ska hitta *alla* element
    # med samma data-id, inte bara det som klickades.
    html_out = render_html([], [], datetime(2026, 8, 24, 9, 0))
    assert 'querySelectorAll(\'li.entry[data-id="\' + CSS.escape(id) + \'"]\')' in html_out


def test_render_html_entries_carry_published_and_discovered_timestamps():
    m = make_mention(
        title="Uppsalahem-nyhet",
        url="https://example.com/1",
        published_at="Mon, 24 Aug 2026 08:00:00 GMT",
    )
    entry = m.to_dict()
    entry["checked_at"] = "2026-08-24T10:00:00+00:00"

    html_out = render_html([], [entry], datetime(2026, 8, 24, 12, 0))

    published_epoch = datetime(2026, 8, 24, 8, 0, tzinfo=timezone.utc).timestamp()
    discovered_epoch = datetime(2026, 8, 24, 10, 0, tzinfo=timezone.utc).timestamp()
    assert f'data-published-ts="{published_epoch:.0f}"' in html_out
    assert f'data-discovered-ts="{discovered_epoch:.0f}"' in html_out


def test_render_html_falls_back_published_ts_to_discovered_when_unparseable():
    entry = make_mention(title="Utan datum", url="https://example.com/no-date", published_at="").to_dict()
    entry["checked_at"] = "2026-08-24T10:00:00+00:00"

    html_out = render_html([], [entry], datetime(2026, 8, 24, 12, 0))

    discovered_epoch = datetime(2026, 8, 24, 10, 0, tzinfo=timezone.utc).timestamp()
    assert f'data-published-ts="{discovered_epoch:.0f}"' in html_out
    assert f'data-discovered-ts="{discovered_epoch:.0f}"' in html_out


def test_render_html_includes_sort_select_with_all_options():
    m = make_mention()
    html_out = render_html([], [m.to_dict()], datetime(2026, 8, 24, 9, 0))

    assert 'id="sort-select"' in html_out
    for value, label in [
        ("published_desc", "Publicerad (senaste först)"),
        ("published_asc", "Publicerad (äldsta först)"),
        ("discovered_desc", "Upptäckt av verktyget (senaste först)"),
        ("discovered_asc", "Upptäckt av verktyget (äldsta först)"),
    ]:
        assert f'<option value="{value}">{label}</option>' in html_out


def test_render_html_filter_bar_lists_present_sources_in_canonical_order():
    reddit = Mention(source="reddit", category="socialt", title="Reddit-inlägg", url="https://example.com/r")
    google = make_mention(title="Google-artikel", url="https://example.com/g")
    entries = [reddit.to_dict(), google.to_dict()]

    html_out = render_html([], entries, datetime(2026, 8, 24, 9, 0))

    # google_news kommer före reddit i den kanoniska ordningen, oavsett
    # ordningen de skickades in i.
    assert html_out.index('value="google_news"') < html_out.index('value="reddit"')
    assert "Google News" in html_out
    assert "Reddit" in html_out


def test_render_html_omits_controls_bar_when_no_data():
    html_out = render_html([], [], datetime(2026, 8, 24, 9, 0))
    assert "Visa källor" not in html_out
    assert '<div class="controls-bar">' not in html_out
    assert 'id="sort-select"' not in html_out


def test_render_html_entries_include_three_weight_buttons():
    m = make_mention()
    html_out = render_html([], [m.to_dict()], datetime(2026, 8, 24, 9, 0))

    assert 'class="weight-buttons"' in html_out
    for value in ("negative", "neutral", "positive"):
        assert f'class="weight-btn weight-{value}" data-weight="{value}"' in html_out


def test_render_html_controls_bar_includes_weight_filter_chips():
    m = make_mention()
    html_out = render_html([], [m.to_dict()], datetime(2026, 8, 24, 9, 0))

    assert "Visa vikt" in html_out
    for value, label in [
        ("positive", "Positiv"),
        ("neutral", "Neutral"),
        ("negative", "Negativ"),
        ("none", "Ej viktad"),
    ]:
        assert f'class="chip chip-weight chip-weight-{value}"' in html_out
        assert f'<input type="checkbox" class="weight-filter" value="{value}" checked>{label}' in html_out


def test_render_html_script_supports_toggling_and_persisting_weights():
    # Skydd mot regression för viktningslogiken i klientens JS.
    html_out = render_html([], [], datetime(2026, 8, 24, 9, 0))
    assert "uppsalahem-monitor:weights" in html_out
    assert "uppsalahem-monitor:hidden-weights" in html_out
    assert "function setWeight(id, value)" in html_out
    assert "function applyWeightState()" in html_out
    # Klick på en redan vald vikt ska växla tillbaka till "ej viktad".
    assert 'setWeight(id, current === value ? "none" : value)' in html_out


class TestParseAnyDatetime:
    def test_parses_rfc822_rss_date(self):
        dt = _parse_any_datetime("Mon, 24 Aug 2026 08:00:00 GMT")
        assert dt == datetime(2026, 8, 24, 8, 0, tzinfo=timezone.utc)

    def test_parses_iso_with_offset(self):
        dt = _parse_any_datetime("2026-08-23T14:22:00+00:00")
        assert dt == datetime(2026, 8, 23, 14, 22, tzinfo=timezone.utc)

    def test_parses_iso_with_trailing_z_and_milliseconds(self):
        dt = _parse_any_datetime("2026-08-24T08:00:00.000Z")
        assert dt == datetime(2026, 8, 24, 8, 0, tzinfo=timezone.utc)

    def test_returns_none_for_empty_or_garbage(self):
        assert _parse_any_datetime("") is None
        assert _parse_any_datetime("inte ett datum") is None
