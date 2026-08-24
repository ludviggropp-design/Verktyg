"""Källa: Reddit – sociala medier (publikt sök-API, ingen nyckel krävs)."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

import requests

from ..config import REQUEST_TIMEOUT, USER_AGENT
from ..models import Mention
from .base import contains_term

SEARCH_URL = "https://www.reddit.com/search.json?q={query}&sort=new&limit=25&t=year"


def fetch(search_term: str) -> list[Mention]:
    """Hämtar Reddit-inlägg som nämner `search_term`."""
    url = SEARCH_URL.format(query=quote_plus(search_term))
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return _parse_response(resp.json(), search_term)


def _parse_response(payload: dict, search_term: str) -> list[Mention]:
    mentions: list[Mention] = []
    children = payload.get("data", {}).get("children", [])
    for child in children:
        post = child.get("data", {})
        title = post.get("title", "") or ""
        selftext = post.get("selftext", "") or ""
        permalink = post.get("permalink", "")
        if not permalink:
            continue
        url = f"https://www.reddit.com{permalink}"

        if not (contains_term(title, search_term) or contains_term(selftext, search_term)):
            continue

        created_utc = post.get("created_utc")
        published_at = ""
        if created_utc:
            published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

        subreddit = post.get("subreddit_name_prefixed", "") or post.get("subreddit", "")
        author = post.get("author", "")

        mentions.append(
            Mention(
                source="reddit",
                category="socialt",
                title=title,
                url=url,
                snippet=selftext[:500],
                author=f"u/{author} ({subreddit})" if author else subreddit,
                published_at=published_at,
            )
        )
    return mentions
