"""Källa: Google News RSS – redaktionellt material, brett sök på sökordet
över alla svenska nyhetssajter Google indexerar.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from ..models import Mention
from .rss_utils import fetch_rss_bytes, items_to_mentions, parse_rss_items

RSS_URL = "https://news.google.com/rss/search?q={query}&hl=sv&gl=SE&ceid=SE:sv"


def fetch(search_term: str) -> list[Mention]:
    """Hämtar nyhetsartiklar från Google News RSS som nämner `search_term`."""
    url = RSS_URL.format(query=quote_plus(search_term))
    xml_bytes = fetch_rss_bytes(url)
    items = parse_rss_items(xml_bytes)
    return items_to_mentions(items, search_term, source="google_news", category="redaktionellt")
