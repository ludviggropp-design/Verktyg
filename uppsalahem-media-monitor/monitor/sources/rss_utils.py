"""Delad logik för alla RSS-baserade källor (Google News, SVT Uppsala,
SR/P4 Uppland m.fl.) – hämtning, generisk RSS 2.0-parsning och filtrering.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import requests

from ..config import REQUEST_TIMEOUT, USER_AGENT
from ..models import Mention
from .base import contains_term

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return _TAG_RE.sub("", text or "").strip()


def fetch_rss_bytes(url: str) -> bytes:
    """Hämtar en RSS-feed som råa bytes."""
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.content


def parse_rss_items(xml_bytes: bytes) -> list[dict]:
    """Parsar en generisk RSS 2.0-feed (<channel><item>...) till enkla dict:ar.

    Fungerar för både nyhets- och poddfeeds så länge de följer standard-RSS,
    vilket Google News, SVT och Sveriges Radios feeds gör.
    """
    items = []
    root = ET.fromstring(xml_bytes)
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = strip_html(item.findtext("description") or "")
        source_el = item.find("source")
        publisher = (source_el.text or "").strip() if source_el is not None else ""

        items.append(
            {
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "description": description,
                "publisher": publisher,
            }
        )
    return items


def items_to_mentions(
    items: list[dict], search_term: str, source: str, category: str
) -> list[Mention]:
    """Filtrerar parsade RSS-poster på sökordet och bygger `Mention`-objekt."""
    mentions: list[Mention] = []
    for it in items:
        if not it["link"]:
            continue
        # Extra säkerhetsfilter: titel eller beskrivning ska faktiskt
        # innehålla sökordet (feeden i sig kan vara obegränsad eller
        # ha en generös sökning).
        if not (contains_term(it["title"], search_term) or contains_term(it["description"], search_term)):
            continue

        mentions.append(
            Mention(
                source=source,
                category=category,
                title=it["title"],
                url=it["link"],
                snippet=it["description"],
                author=it["publisher"],
                published_at=it["pub_date"],
            )
        )
    return mentions
