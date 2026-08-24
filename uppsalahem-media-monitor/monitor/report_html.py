"""Genererar en lokal HTML-rapport (data/report.html) med bevakningens
resultat. Detta är gränssnittet de flesta användare möter – de dubbelklickar
på lanseringsskriptet, som öppnar den här sidan i webbläsaren, istället för
att läsa terminalens textutskrift.
"""

from __future__ import annotations

import html
from datetime import datetime

from .models import Mention

_SWEDISH_MONTHS = [
    "januari", "februari", "mars", "april", "maj", "juni",
    "juli", "augusti", "september", "oktober", "november", "december",
]

_SOURCE_LABELS = {
    "google_news": "Google News",
    "svt_uppsala": "SVT Uppsala",
    "sr_uppland": "SR / P4 Uppland",
    "reddit": "Reddit",
    "bluesky": "Bluesky",
}

# Tak för hur många historikposter som ritas ut, så filen inte växer sig
# orimligt stor efter månader av körningar.
MAX_HISTORY_ITEMS = 500

# Filnamnet rapporten skrivs till i datakatalogen.
REPORT_FILENAME = "report.html"


def _format_checked_at(dt: datetime) -> str:
    return f"{dt.day} {_SWEDISH_MONTHS[dt.month - 1]} {dt.year}, {dt.strftime('%H:%M')}"


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _source_label(source: str) -> str:
    return _SOURCE_LABELS.get(source, source)


def _render_entry(entry: dict, is_new: bool) -> str:
    badge = '<span class="badge">NY</span>' if is_new else ""
    meta_bits = []
    if entry.get("author"):
        meta_bits.append(f'<span>{_esc(entry["author"])}</span>')
    if entry.get("published_at"):
        meta_bits.append(f'<span>{_esc(entry["published_at"])}</span>')
    meta = f'<div class="entry-meta">{"".join(meta_bits)}</div>' if meta_bits else ""
    snippet = f'<p class="snippet">{_esc(entry.get("snippet", ""))}</p>' if entry.get("snippet") else ""

    return f"""<li class="entry">
        <div class="entry-head">
          <span class="source-tag">{_esc(_source_label(entry.get("source", "")))}</span>
          {badge}
        </div>
        <a class="entry-title" href="{_esc(entry.get("url", "#"))}" target="_blank" rel="noopener">{_esc(entry.get("title", ""))}</a>
        {snippet}
        {meta}
      </li>"""


def render_html(new_mentions: list[Mention], all_entries: list[dict], checked_at: datetime) -> str:
    """Bygger en fristående HTML-sida med dagens och tidigare träffar."""
    new_ids = {m.id for m in new_mentions}

    by_category: dict[str, list[Mention]] = {}
    for m in new_mentions:
        by_category.setdefault(m.category, []).append(m)

    if new_mentions:
        category_sections = ""
        for category, label in (("redaktionellt", "Redaktionellt"), ("socialt", "Socialt")):
            items = by_category.get(category, [])
            if not items:
                continue
            rows = "".join(_render_entry(m.to_dict(), is_new=True) for m in items)
            category_sections += f'<h3 class="category-title">{label}</h3><ul class="entries">{rows}</ul>'
        new_section = f"""<section class="panel highlight">
        <h2>&#128276; {len(new_mentions)} ny(a) nämning(ar) sedan förra kontrollen</h2>
        {category_sections}
      </section>"""
    else:
        new_section = """<section class="panel quiet">
        <h2>Inga nya nämningar sedan förra kontrollen</h2>
        <p>Allt är precis som förut just nu. Kör verktyget igen senare för att kolla på nytt.</p>
      </section>"""

    history = sorted(all_entries, key=lambda e: e.get("checked_at", ""), reverse=True)
    truncated = len(history) > MAX_HISTORY_ITEMS
    shown = history[:MAX_HISTORY_ITEMS]
    history_rows = "".join(_render_entry(e, is_new=e.get("id") in new_ids) for e in shown)
    if not history_rows:
        history_rows = '<li class="empty">Inga nämningar hittade ännu.</li>'
    truncation_note = (
        f'<p class="truncation">Visar de {MAX_HISTORY_ITEMS} senaste av {len(history)} nämningar totalt.</p>'
        if truncated
        else ""
    )

    return f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Uppsalahem – omvärldsbevakning</title>
<style>{_STYLE}</style>
</head>
<body>
<main>
  <header>
    <p class="eyebrow">Omvärldsbevakning</p>
    <h1>Uppsalahem i media och sociala kanaler</h1>
    <p class="checked-at">Senast kontrollerad: {_esc(_format_checked_at(checked_at))}</p>
  </header>

  {new_section}

  <section class="panel">
    <h2>Alla nämningar hittills <span class="count">({len(history)})</span></h2>
    {truncation_note}
    <ul class="entries">{history_rows}</ul>
  </section>

  <footer>
    <p>Genererad automatiskt av omvärldsbevakaren. Dubbelklicka på lanseringsskriptet igen för att uppdatera den här sidan.</p>
  </footer>
</main>
</body>
</html>
"""


_STYLE = """
:root {
  --paper: #f2f4f3;
  --paper-raised: #ffffff;
  --ink: #1e2a28;
  --ink-soft: #4b5b58;
  --ink-faint: #7c8a86;
  --line: #d8dfdb;
  --accent: #2f6f5e;
  --accent-strong: #1f5445;
  --accent-soft: #e3efec;
}

@media (prefers-color-scheme: dark) {
  :root {
    --paper: #141b1a;
    --paper-raised: #1b2422;
    --ink: #eef2f0;
    --ink-soft: #b7c4c0;
    --ink-faint: #7f8d89;
    --line: #2c3735;
    --accent: #6fc8ab;
    --accent-strong: #8ad8bd;
    --accent-soft: #223330;
  }
}

* { box-sizing: border-box; }

body {
  background: var(--paper);
  color: var(--ink);
  font-family: "Segoe UI", "Segoe UI Variable", system-ui, -apple-system, sans-serif;
  font-size: 16px;
  line-height: 1.55;
  margin: 0;
  padding: 0 20px 64px;
}

main { max-width: 720px; margin: 0 auto; }

h1, h2, h3 {
  font-family: Constantia, Georgia, "Iowan Old Style", serif;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.25;
}

header { padding: 48px 0 28px; }

.eyebrow {
  font-size: 12.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-strong);
  margin: 0 0 10px;
}

h1 { font-size: clamp(26px, 4.5vw, 34px); margin: 0 0 10px; }

.checked-at { color: var(--ink-soft); margin: 0; font-size: 14.5px; }

.panel {
  background: var(--paper-raised);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 24px 26px;
  margin-bottom: 22px;
  box-shadow: 0 1px 2px rgba(30, 42, 40, 0.06), 0 8px 24px -12px rgba(30, 42, 40, 0.16);
}

.panel.highlight { border-color: var(--accent); background: var(--accent-soft); }
.panel.quiet { color: var(--ink-soft); }
.panel h2 { font-size: 19px; margin: 0 0 10px; }
.panel.quiet p { margin: 0; }

.count { color: var(--ink-faint); font-weight: 400; font-size: 15px; }

.category-title {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-faint);
  margin: 18px 0 8px;
}
.category-title:first-of-type { margin-top: 4px; }

ul.entries { list-style: none; margin: 0; padding: 0; }

li.entry {
  padding: 14px 0;
  border-top: 1px solid var(--line);
}
li.entry:first-child { border-top: none; padding-top: 0; }

li.empty {
  color: var(--ink-faint);
  padding: 4px 0;
}

.entry-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.source-tag {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--accent-strong);
  background: var(--accent-soft);
  border-radius: 999px;
  padding: 2px 10px;
}

.badge {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #ffffff;
  background: var(--accent);
  border-radius: 5px;
  padding: 1px 6px;
}

a.entry-title {
  display: block;
  font-weight: 600;
  color: var(--ink);
  text-decoration: none;
  font-size: 16px;
  margin-bottom: 4px;
}
a.entry-title:hover { color: var(--accent-strong); text-decoration: underline; }

.snippet {
  color: var(--ink-soft);
  font-size: 14.5px;
  margin: 0 0 6px;
}

.entry-meta {
  display: flex;
  gap: 14px;
  color: var(--ink-faint);
  font-size: 13px;
}

.truncation { color: var(--ink-faint); font-size: 13.5px; margin: 0 0 12px; }

footer {
  color: var(--ink-faint);
  font-size: 13px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}
"""
