"""Källa: Bing News RSS – redaktionellt material, brett sök på sökordet över
alla nyhetssajter Bing indexerar. Ett komplement till Google News: annat
sökindex, andra träffar ibland.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from ..models import Mention
from .rss_utils import fetch_rss_bytes, items_to_mentions, parse_rss_items

RSS_URL = "https://www.bing.com/news/search?q={query}&format=rss"


def fetch(search_term: str) -> list[Mention]:
    """Hämtar nyhetsartiklar från Bing News RSS som nämner `search_term`."""
    url = RSS_URL.format(query=quote_plus(search_term))
    xml_bytes = fetch_rss_bytes(url)
    items = parse_rss_items(xml_bytes)
    return items_to_mentions(items, search_term, source="bing_news", category="redaktionellt")
