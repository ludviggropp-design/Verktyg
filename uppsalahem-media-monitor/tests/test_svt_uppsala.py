from monitor.sources import svt_uppsala

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<item>
<title>Uppsalahem höjer hyrorna nästa år</title>
<link>https://www.svt.se/nyheter/lokalt/uppsala/artikel-1</link>
<pubDate>Mon, 24 Aug 2026 08:00:00 GMT</pubDate>
<description>Kommunala bostadsbolaget Uppsalahem meddelar hyreshöjning.</description>
</item>
<item>
<title>Ny cykelbana invigd i Uppsala</title>
<link>https://www.svt.se/nyheter/lokalt/uppsala/artikel-2</link>
<pubDate>Mon, 24 Aug 2026 09:00:00 GMT</pubDate>
<description>Nämner inte sökordet.</description>
</item>
</channel>
</rss>
"""


def test_fetch_uses_fixed_local_url_and_filters(monkeypatch):
    captured = {}

    def fake_fetch_rss_bytes(url):
        captured["url"] = url
        return SAMPLE_RSS.encode("utf-8")

    monkeypatch.setattr(svt_uppsala, "fetch_rss_bytes", fake_fetch_rss_bytes)

    mentions = svt_uppsala.fetch("Uppsalahem")

    assert captured["url"] == svt_uppsala.RSS_URL
    assert "uppsala" in captured["url"]
    assert len(mentions) == 1
    assert mentions[0].source == "svt_uppsala"
    assert mentions[0].category == "redaktionellt"
    assert mentions[0].url == "https://www.svt.se/nyheter/lokalt/uppsala/artikel-1"
