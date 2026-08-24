from monitor.sources import reddit

SAMPLE_PAYLOAD = {
    "data": {
        "children": [
            {
                "data": {
                    "title": "Flyttade nyligen till en lägenhet hos Uppsalahem",
                    "selftext": "Väldigt nöjd hittills!",
                    "permalink": "/r/uppsala/comments/abc123/flyttade_nyligen/",
                    "author": "en_uppsalabo",
                    "subreddit_name_prefixed": "r/uppsala",
                    "created_utc": 1750000000,
                }
            },
            {
                "data": {
                    "title": "Helt orelaterat inlägg",
                    "selftext": "Nämner inte sökordet.",
                    "permalink": "/r/random/comments/xyz789/orelaterat/",
                    "author": "nagon_annan",
                    "subreddit_name_prefixed": "r/random",
                    "created_utc": 1750000001,
                }
            },
        ]
    }
}


def test_parse_response_filters_by_term():
    mentions = reddit._parse_response(SAMPLE_PAYLOAD, "Uppsalahem")

    assert len(mentions) == 1
    m = mentions[0]
    assert m.source == "reddit"
    assert m.category == "socialt"
    assert m.url == "https://www.reddit.com/r/uppsala/comments/abc123/flyttade_nyligen/"
    assert m.author == "u/en_uppsalabo (r/uppsala)"
    assert m.published_at  # ska ha konverterats till ISO-sträng


def test_fetch_wires_requests(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return SAMPLE_PAYLOAD

    def fake_get(url, headers=None, timeout=None):
        assert "Uppsalahem" in url
        assert headers["User-Agent"]
        return FakeResponse()

    monkeypatch.setattr(reddit.requests, "get", fake_get)

    mentions = reddit.fetch("Uppsalahem")
    assert len(mentions) == 1
