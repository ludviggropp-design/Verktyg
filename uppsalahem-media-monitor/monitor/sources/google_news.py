"""Källa: Google News RSS – redaktionellt material (nyheter/press)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import requests

from ..config import REQUEST_TIMEOUT, USER_AGENT
from ..models import Mention
from .base import contains_term

RSS_URL = "https://news.google.com/rss/search?q={query}&hl=sv&gl=SE&ceid=SE:sv"

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text or "").strip()


def fetch(search_term: str) -> list[Mention]:
    """Hämtar nyhetsartiklar från Google News RSS som nämner `search_term`."""
    url = RSS_URL.format(query=quote_plus(search_term))
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return _parse_rss(resp.content, search_term)


def _parse_rss(xml_bytes: bytes, search_term: str) -> list[Mention]:
    mentions: list[Mention] = []
    root = ET.fromstring(xml_bytes)
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = _strip_html(item.findtext("description") or "")
        source_el = item.find("source")
        publisher = (source_el.text or "").strip() if source_el is not None else ""

        if not link:
            continue
        # Extra säkerhetsfilter: titel eller beskrivning ska faktiskt
        # innehålla sökordet (RSS-sökningen kan ibland vara generös).
        if not (contains_term(title, search_term) or contains_term(description, search_term)):
            continue

        mentions.append(
            Mention(
                source="google_news",
                category="redaktionellt",
                title=title,
                url=link,
                snippet=description,
                author=publisher,
                published_at=pub_date,
            )
        )
    return mentions
