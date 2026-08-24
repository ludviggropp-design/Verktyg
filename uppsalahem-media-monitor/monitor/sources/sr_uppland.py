"""Källa: Sveriges Radio P4 Uppland (SR Uppland) – riktat redaktionellt flöde.

Använder Sveriges Radios öppna RSS-API för programmet P4 Uppland
(programid 114). Precis som SVT-flödet är detta ett fast lokalt flöde utan
sökord i URL:en – filtreringen sker i `items_to_mentions` mot titel/
beskrivning för varje avsnitt/inslag.

Notera: eftersom SR:s feed är radioavsnitt hittas bara nämningar som också
syns i avsnittens text (titel/beskrivning), inte allt som sägs i sändning.
"""

from __future__ import annotations

from ..models import Mention
from .rss_utils import fetch_rss_bytes, items_to_mentions, parse_rss_items

SR_P4_UPPLAND_PROGRAM_ID = 114
RSS_URL = f"https://api.sr.se/api/rss/program/{SR_P4_UPPLAND_PROGRAM_ID}"


def fetch(search_term: str) -> list[Mention]:
    """Hämtar avsnitt/inslag från P4 Uppland som nämner `search_term`."""
    xml_bytes = fetch_rss_bytes(RSS_URL)
    items = parse_rss_items(xml_bytes)
    return items_to_mentions(items, search_term, source="sr_uppland", category="redaktionellt")
