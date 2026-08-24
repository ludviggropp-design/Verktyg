from monitor.sources import rss_utils

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Exempelflöde</title>
<item>
<title>Uppsalahem bygger 200 nya lägenheter i Gottsunda</title>
<link>https://example.com/artikel-1</link>
<pubDate>Mon, 24 Aug 2026 08:00:00 GMT</pubDate>
<description>&lt;a href="https://example.com/artikel-1"&gt;Uppsalahem planerar nybyggnation&lt;/a&gt;&amp;nbsp;i Uppsala.</description>
<source url="https://example.com">Exempel Nyheter</source>
</item>
<item>
<title>Annat bostadsbolag expanderar</title>
<link>https://example.com/artikel-2</link>
<pubDate>Mon, 24 Aug 2026 09:00:00 GMT</pubDate>
<description>Text som inte nämner sökordet alls.</description>
</item>
<item>
<title>Post utan länk ska hoppas över</title>
<link></link>
<description>Uppsalahem nämns här men saknar länk.</description>
</item>
</channel>
</rss>
"""


def test_parse_rss_items_extracts_all_items():
    items = rss_utils.parse_rss_items(SAMPLE_RSS.encode("utf-8"))

    assert len(items) == 3
    first = items[0]
    assert first["title"] == "Uppsalahem bygger 200 nya lägenheter i Gottsunda"
    assert first["link"] == "https://example.com/artikel-1"
    assert first["publisher"] == "Exempel Nyheter"
    assert "<a" not in first["description"]  # HTML-taggar bortstrippade

    second = items[1]
    assert second["publisher"] == ""  # ingen <source>-tagg


def test_items_to_mentions_filters_by_term_and_requires_link():
    items = rss_utils.parse_rss_items(SAMPLE_RSS.encode("utf-8"))
    mentions = rss_utils.items_to_mentions(
        items, "Uppsalahem", source="test_source", category="redaktionellt"
    )

    assert len(mentions) == 1
    m = mentions[0]
    assert m.source == "test_source"
    assert m.category == "redaktionellt"
    assert m.url == "https://example.com/artikel-1"


def test_fetch_rss_bytes_wires_requests(monkeypatch):
    captured = {}

    class FakeResponse:
        content = SAMPLE_RSS.encode("utf-8")

        def raise_for_status(self):
            return None

    def fake_get(url, headers=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr(rss_utils.requests, "get", fake_get)

    content = rss_utils.fetch_rss_bytes("https://example.com/feed.xml")

    assert content == SAMPLE_RSS.encode("utf-8")
    assert captured["url"] == "https://example.com/feed.xml"
    assert "User-Agent" in captured["headers"]
