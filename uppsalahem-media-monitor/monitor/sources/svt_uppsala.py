"""Källa: SVT Nyheter Uppsala – riktat redaktionellt flöde.

Till skillnad från Google News är detta ett fast lokalt nyhetsflöde (inget
sökord i själva URL:en), så filtreringen på sökordet sker helt i
`items_to_mentions`.
"""

from __future__ import annotations

from ..models import Mention
from .rss_utils import fetch_rss_bytes, items_to_mentions, parse_rss_items

RSS_URL = "https://www.svt.se/nyheter/lokalt/uppsala/rss.xml"


def fetch(search_term: str) -> list[Mention]:
    """Hämtar SVT Uppsalas lokala nyheter som nämner `search_term`."""
    xml_bytes = fetch_rss_bytes(RSS_URL)
    items = parse_rss_items(xml_bytes)
    return items_to_mentions(items, search_term, source="svt_uppsala", category="redaktionellt")
