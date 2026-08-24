"""Datamodell för en enskild bevakningsträff."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class Mention:
    """En träff där sökordet (t.ex. "Uppsalahem") nämns."""

    source: str  # t.ex. "google_news", "reddit", "bluesky"
    category: str  # "redaktionellt" eller "socialt"
    title: str
    url: str
    snippet: str = ""
    author: str = ""
    published_at: str = ""  # ISO 8601-sträng, tom om okänt
    id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.id:
            # Stabilt id för deduplicering, baserat på källa + url.
            basis = f"{self.source}:{self.url}".encode("utf-8")
            self.id = hashlib.sha256(basis).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "category": self.category,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "author": self.author,
            "published_at": self.published_at,
        }
