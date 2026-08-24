from monitor.sources import bluesky

SAMPLE_PAYLOAD = {
    "posts": [
        {
            "uri": "at://did:plc:abc123/app.bsky.feed.post/xyz789",
            "author": {"handle": "boende.bsky.social"},
            "record": {
                "text": "Precis skrivit kontrakt hos Uppsalahem, kul!",
                "createdAt": "2026-08-24T08:00:00.000Z",
            },
        },
        {
            "uri": "at://did:plc:def456/app.bsky.feed.post/uvw123",
            "author": {"handle": "annan.bsky.social"},
            "record": {
                "text": "Ett inlägg som inte nämner sökordet.",
                "createdAt": "2026-08-24T09:00:00.000Z",
            },
        },
    ]
}


def test_parse_response_filters_by_term():
    mentions = bluesky._parse_response(SAMPLE_PAYLOAD, "Uppsalahem")

    assert len(mentions) == 1
    m = mentions[0]
    assert m.source == "bluesky"
    assert m.category == "socialt"
    assert m.url == "https://bsky.app/profile/boende.bsky.social/post/xyz789"
    assert m.author == "@boende.bsky.social"


def test_fetch_wires_requests(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return SAMPLE_PAYLOAD

    def fake_get(url, headers=None, timeout=None):
        assert "Uppsalahem" in url
        return FakeResponse()

    monkeypatch.setattr(bluesky.requests, "get", fake_get)

    mentions = bluesky.fetch("Uppsalahem")
    assert len(mentions) == 1
