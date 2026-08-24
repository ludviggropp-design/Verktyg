from monitor.sources import sr_uppland

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<item>
<title>Uppsalahem investerar i nya bostäder</title>
<link>https://sverigesradio.se/avsnitt/1</link>
<pubDate>Mon, 24 Aug 2026 08:00:00 GMT</pubDate>
<description>Reportage om Uppsalahems nybyggnation i Uppland.</description>
</item>
<item>
<title>Trafikläget i Uppland</title>
<link>https://sverigesradio.se/avsnitt/2</link>
<pubDate>Mon, 24 Aug 2026 09:00:00 GMT</pubDate>
<description>Nämner inte sökordet.</description>
</item>
</channel>
</rss>
"""


def test_fetch_uses_p4_uppland_program_feed_and_filters(monkeypatch):
    captured = {}

    def fake_fetch_rss_bytes(url):
        captured["url"] = url
        return SAMPLE_RSS.encode("utf-8")

    monkeypatch.setattr(sr_uppland, "fetch_rss_bytes", fake_fetch_rss_bytes)

    mentions = sr_uppland.fetch("Uppsalahem")

    assert captured["url"] == sr_uppland.RSS_URL
    assert "api.sr.se/api/rss/program/114" in captured["url"]
    assert len(mentions) == 1
    assert mentions[0].source == "sr_uppland"
    assert mentions[0].category == "redaktionellt"
    assert mentions[0].url == "https://sverigesradio.se/avsnitt/1"
