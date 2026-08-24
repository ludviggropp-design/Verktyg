from monitor.sources import google_news

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<item>
<title>Uppsalahem bygger 200 nya lägenheter i Gottsunda</title>
<link>https://example.com/artikel-1</link>
<pubDate>Mon, 24 Aug 2026 08:00:00 GMT</pubDate>
<description>Uppsalahem planerar nybyggnation i Uppsala.</description>
<source url="https://example.com">Exempel Nyheter</source>
</item>
<item>
<title>Annat bostadsbolag expanderar</title>
<link>https://example.com/artikel-2</link>
<pubDate>Mon, 24 Aug 2026 09:00:00 GMT</pubDate>
<description>Text som inte nämner sökordet alls.</description>
</item>
</channel>
</rss>
"""


def test_fetch_uses_query_url_and_filters(monkeypatch):
    captured = {}

    def fake_fetch_rss_bytes(url):
        captured["url"] = url
        return SAMPLE_RSS.encode("utf-8")

    monkeypatch.setattr(google_news, "fetch_rss_bytes", fake_fetch_rss_bytes)

    mentions = google_news.fetch("Uppsalahem")

    assert "Uppsalahem" in captured["url"]
    assert "news.google.com/rss/search" in captured["url"]
    assert len(mentions) == 1
    assert mentions[0].source == "google_news"
    assert mentions[0].category == "redaktionellt"
    assert mentions[0].url == "https://example.com/artikel-1"
