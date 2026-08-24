"""Konfiguration för omvärldsbevakaren."""

from __future__ import annotations

import os
from pathlib import Path

# Standardsökord. Kan skrivas över med --search-term.
DEFAULT_SEARCH_TERM = "Uppsalahem"

# Vilka källor som är aktiva som standard. Kan skrivas över med --sources.
DEFAULT_SOURCES = ["google_news", "svt_uppsala", "sr_uppland", "reddit", "bluesky"]

# Var bevakningens tillstånd (sedda träffar + logg) sparas.
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = Path(os.environ.get("MONITOR_DATA_DIR", BASE_DIR / "data"))

# HTTP-timeout i sekunder för alla källor.
REQUEST_TIMEOUT = 15

# User-Agent som skickas till externa tjänster. Reddit och andra tjänster
# svarar med fel/blockering om denna saknas eller är för generisk.
USER_AGENT = "uppsalahem-media-monitor/1.0 (+omvarldsbevakning)"
