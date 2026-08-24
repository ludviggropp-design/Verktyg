"""Håller reda på vilka träffar som redan rapporterats (deduplicering)
samt en historikslogg över alla träffar som någonsin hittats.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import Mention

SEEN_FILENAME = "seen.json"
LOG_FILENAME = "log.jsonl"


class State:
    """Läser/skriver deduplicerings- och logg-filer i en datakatalog."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.seen_path = self.data_dir / SEEN_FILENAME
        self.log_path = self.data_dir / LOG_FILENAME
        self._seen_ids: set[str] = self._load_seen()

    def _load_seen(self) -> set[str]:
        if not self.seen_path.exists():
            return set()
        try:
            with self.seen_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return set(data.get("seen_ids", []))
        except (json.JSONDecodeError, OSError):
            # Trasig eller ofullständig fil ska inte krascha bevakningen –
            # hellre rapportera om en träff igen än att tappa körningen.
            return set()

    def is_new(self, mention: Mention) -> bool:
        return mention.id not in self._seen_ids

    def mark_seen(self, mentions: list[Mention]) -> None:
        for m in mentions:
            self._seen_ids.add(m.id)

    def save(self) -> None:
        with self.seen_path.open("w", encoding="utf-8") as fh:
            json.dump({"seen_ids": sorted(self._seen_ids)}, fh, ensure_ascii=False, indent=2)

    def append_log(self, mentions: list[Mention]) -> None:
        if not mentions:
            return
        checked_at = datetime.now(timezone.utc).isoformat()
        with self.log_path.open("a", encoding="utf-8") as fh:
            for m in mentions:
                entry = m.to_dict()
                entry["checked_at"] = checked_at
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_log(self) -> list[dict]:
        """Läser hela historikloggen (alla träffar som någonsin hittats)."""
        if not self.log_path.exists():
            return []
        entries: list[dict] = []
        with self.log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    # En trasig rad ska inte välta hela rapporten.
                    continue
        return entries
