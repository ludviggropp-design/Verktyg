from monitor.sources import google_news

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>"Uppsalahem" - Google Nyheter</title>
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
<source url="https://example.com">Exempel Nyheter</source>
</item>
</channel>
</rss>
"""


def test_parse_rss_extracts_matching_items():
    mentions = google_news._parse_rss(SAMPLE_RSS.encode("utf-8"), "Uppsalahem")

    assert len(mentions) == 1
    m = mentions[0]
    assert m.source == "google_news"
    assert m.category == "redaktionellt"
    assert m.url == "https://example.com/artikel-1"
    assert "Uppsalahem" in m.title
    assert m.author == "Exempel Nyheter"
    assert "<a" not in m.snippet  # HTML-taggar ska vara bortstrippade


def test_parse_rss_filters_out_non_matching_items():
    mentions = google_news._parse_rss(SAMPLE_RSS.encode("utf-8"), "Uppsalahem")
    urls = [m.url for m in mentions]
    assert "https://example.com/artikel-2" not in urls


def test_fetch_uses_requests_and_parses(monkeypatch):
    captured = {}

    class FakeResponse:
        content = SAMPLE_RSS.encode("utf-8")

        def raise_for_status(self):
            return None

    def fake_get(url, headers=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr(google_news.requests, "get", fake_get)

    mentions = google_news.fetch("Uppsalahem")

    assert len(mentions) == 1
    assert "Uppsalahem" in captured["url"]
    assert "User-Agent" in captured["headers"]
