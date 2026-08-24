"""Källa: Bluesky – sociala medier (publikt AT Protocol-API, ingen nyckel krävs)."""

from __future__ import annotations

from urllib.parse import quote_plus

import requests

from ..config import REQUEST_TIMEOUT, USER_AGENT
from ..models import Mention
from .base import contains_term

SEARCH_URL = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q={query}&limit=25"


def fetch(search_term: str) -> list[Mention]:
    """Hämtar Bluesky-inlägg som nämner `search_term`."""
    url = SEARCH_URL.format(query=quote_plus(search_term))
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return _parse_response(resp.json(), search_term)


def _parse_response(payload: dict, search_term: str) -> list[Mention]:
    mentions: list[Mention] = []
    posts = payload.get("posts", [])
    for post in posts:
        record = post.get("record", {}) or {}
        text = record.get("text", "") or ""
        if not contains_term(text, search_term):
            continue

        author = post.get("author", {}) or {}
        handle = author.get("handle", "")
        uri = post.get("uri", "")
        rkey = uri.rsplit("/", 1)[-1] if uri else ""
        if not handle or not rkey:
            continue
        url = f"https://bsky.app/profile/{handle}/post/{rkey}"

        mentions.append(
            Mention(
                source="bluesky",
                category="socialt",
                title=text[:120],
                url=url,
                snippet=text,
                author=f"@{handle}",
                published_at=record.get("createdAt", ""),
            )
        )
    return mentions
