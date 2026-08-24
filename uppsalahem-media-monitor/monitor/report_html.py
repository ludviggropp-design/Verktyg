"""Genererar en lokal HTML-rapport (data/report.html) med bevakningens
resultat. Detta är gränssnittet de flesta användare möter – de dubbelklickar
på lanseringsskriptet, som öppnar den här sidan i webbläsaren, istället för
att läsa terminalens textutskrift.

Sidan har lite egen JavaScript-logik (ingen server, allt lokalt i
webbläsaren):
- Nämningar sorteras efter när nyheten faktiskt publicerades, inte när
  verktyget hittade den.
- Källfilter (kryssrutor) för att bara visa vissa kanaler, kommer ihåg
  valet i webbläsarens localStorage till nästa körning.
- Klickar man på en artikel markeras den som läst (också i localStorage)
  och NY-märkningen försvinner direkt, utan att sidan behöver laddas om.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

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

# Ordningen källorna visas i (t.ex. i filterraden). Okända källor hamnar
# sist, alfabetiskt.
_SOURCE_ORDER = ["google_news", "svt_uppsala", "sr_uppland", "reddit", "bluesky"]

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


def _ordered_sources(present: set[str]) -> list[str]:
    ordered = [s for s in _SOURCE_ORDER if s in present]
    extra = sorted(present - set(_SOURCE_ORDER))
    return ordered + extra


def _parse_any_datetime(text: str) -> datetime | None:
    """Tolkar både RSS-formatet (RFC 822, t.ex. källorna från Google News/SVT/
    SR) och ISO 8601 (Reddit, Bluesky). Returnerar None om texten inte går
    att tolka, så anroparen kan falla tillbaka på ett annat värde.
    """
    if not text:
        return None
    text = text.strip()

    try:
        dt = parsedate_to_datetime(text)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass

    iso_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        dt = datetime.fromisoformat(iso_text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _sort_key(entry: dict) -> datetime:
    """Sorteringsnyckel: när nyheten publicerades om det går att tolka,
    annars när verktyget upptäckte den, annars längst bak.
    """
    return (
        _parse_any_datetime(entry.get("published_at", ""))
        or _parse_any_datetime(entry.get("checked_at", ""))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _render_entry(entry: dict, is_new: bool) -> str:
    badge = '<span class="badge">NY</span>' if is_new else ""
    meta_bits = []
    if entry.get("author"):
        meta_bits.append(f'<span>{_esc(entry["author"])}</span>')
    if entry.get("published_at"):
        meta_bits.append(f'<span>{_esc(entry["published_at"])}</span>')
    meta = f'<div class="entry-meta">{"".join(meta_bits)}</div>' if meta_bits else ""
    snippet = f'<p class="snippet">{_esc(entry.get("snippet", ""))}</p>' if entry.get("snippet") else ""
    source = entry.get("source", "")

    return f"""<li class="entry" data-id="{_esc(entry.get('id', ''))}" data-source="{_esc(source)}">
        <div class="entry-head">
          <span class="source-tag">{_esc(_source_label(source))}</span>
          {badge}
        </div>
        <a class="entry-title" href="{_esc(entry.get("url", "#"))}" target="_blank" rel="noopener">{_esc(entry.get("title", ""))}</a>
        {snippet}
        {meta}
      </li>"""


def _render_filter_bar(sources_present: list[str]) -> str:
    if not sources_present:
        return ""
    chips = "".join(
        f'<label class="chip">'
        f'<input type="checkbox" class="source-filter" value="{_esc(s)}" checked>'
        f"{_esc(_source_label(s))}</label>"
        for s in sources_present
    )
    return f"""<div class="filter-bar">
    <span class="filter-label">Visa källor</span>
    {chips}
  </div>"""


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
            category_sections += (
                f'<div class="category-group" data-category="{category}">'
                f'<h3 class="category-title">{label}</h3>'
                f'<ul class="entries">{rows}</ul></div>'
            )
        new_section = f"""<section class="panel highlight" id="new-panel">
        <h2>&#128276; <span id="new-count-label">{len(new_mentions)}</span> ny(a) nämning(ar) sedan förra kontrollen</h2>
        {category_sections}
        <p class="filter-empty" id="new-filter-empty" hidden>Inga nya nämningar bland de valda källorna.</p>
      </section>"""
    else:
        new_section = """<section class="panel quiet" id="new-panel">
        <h2>Inga nya nämningar sedan förra kontrollen</h2>
        <p>Allt är precis som förut just nu. Kör verktyget igen senare för att kolla på nytt.</p>
      </section>"""

    history = sorted(all_entries, key=_sort_key, reverse=True)
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

    sources_present = _ordered_sources(
        {m.source for m in new_mentions} | {e.get("source", "") for e in all_entries} - {""}
    )
    filter_bar = _render_filter_bar(sources_present)

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
    <p class="checked-at">Senast kontrollerad: {_esc(_format_checked_at(checked_at))} · sorterat efter publiceringsdatum</p>
  </header>

  {filter_bar}

  {new_section}

  <section class="panel">
    <h2>Alla nämningar hittills <span class="count" id="history-count-label">({len(history)})</span></h2>
    {truncation_note}
    <ul class="entries" id="history-list">{history_rows}</ul>
    <p class="filter-empty" id="history-filter-empty" hidden>Inga nämningar matchar de valda källorna.</p>
  </section>

  <footer>
    <p>Genererad automatiskt av omvärldsbevakaren. Dubbelklicka på lanseringsskriptet igen för att uppdatera den här sidan. Lästa artiklar och valda källfilter sparas i den här webbläsaren.</p>
  </footer>
</main>
<script>{_SCRIPT}</script>
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

header { padding: 48px 0 24px; }

.eyebrow {
  font-size: 12.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-strong);
  margin: 0 0 10px;
}

h1 { font-size: clamp(26px, 4.5vw, 34px); margin: 0 0 10px; }

.checked-at { color: var(--ink-soft); margin: 0; font-size: 14.5px; }

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  margin-bottom: 22px;
  padding: 12px 16px;
  background: var(--paper-raised);
  border: 1px solid var(--line);
  border-radius: 999px;
}

.filter-label {
  font-size: 12.5px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-faint);
  margin-right: 4px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  color: var(--ink-soft);
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 4px 12px 4px 8px;
  cursor: pointer;
  user-select: none;
}

.chip:has(input:checked) {
  color: var(--accent-strong);
  background: var(--accent-soft);
  border-color: var(--accent);
}

.chip input {
  accent-color: var(--accent);
  cursor: pointer;
}

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
.category-group:first-of-type .category-title { margin-top: 4px; }

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

.filter-empty {
  color: var(--ink-faint);
  font-style: italic;
  font-size: 14px;
  margin: 4px 0 0;
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

li.entry.is-read a.entry-title { color: var(--ink-soft); font-weight: 500; }

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

# Ren klientlogik, ingen server: lästa artiklar och källfilter sparas i
# webbläsarens localStorage och gäller alltså den här datorn/webbläsaren.
_SCRIPT = """
(function () {
  var STORAGE_READ = "uppsalahem-monitor:read-ids";
  var STORAGE_HIDDEN = "uppsalahem-monitor:hidden-sources";

  function loadSet(key) {
    try {
      var raw = localStorage.getItem(key);
      var arr = raw ? JSON.parse(raw) : [];
      return new Set(Array.isArray(arr) ? arr : []);
    } catch (e) {
      return new Set();
    }
  }

  function saveSet(key, set) {
    try {
      localStorage.setItem(key, JSON.stringify(Array.from(set)));
    } catch (e) {
      /* t.ex. privat läge utan lagring - fortsätt utan att spara */
    }
  }

  var readIds = loadSet(STORAGE_READ);
  var hiddenSources = loadSet(STORAGE_HIDDEN);

  function markElementRead(li) {
    var badge = li.querySelector(".badge");
    if (badge) badge.remove();
    li.classList.add("is-read");
  }

  function markRead(li) {
    // Samma artikel kan finnas både i "nya sedan sist" och i historiken -
    // markera alla förekomster, inte bara den som klickades.
    var id = li.getAttribute("data-id");
    if (!id) return;
    document.querySelectorAll('li.entry[data-id="' + CSS.escape(id) + '"]').forEach(markElementRead);
    if (!readIds.has(id)) {
      readIds.add(id);
      saveSet(STORAGE_READ, readIds);
    }
  }

  function applyReadState() {
    document.querySelectorAll("li.entry").forEach(function (li) {
      var id = li.getAttribute("data-id");
      if (id && readIds.has(id)) markElementRead(li);
    });
  }

  document.querySelectorAll("li.entry a.entry-title").forEach(function (a) {
    a.addEventListener("click", function () {
      var li = a.closest("li.entry");
      if (li) markRead(li);
    });
  });

  function updateCounts() {
    var historyItems = document.querySelectorAll("#history-list li.entry");
    var historyVisible = 0;
    historyItems.forEach(function (li) { if (li.style.display !== "none") historyVisible++; });
    var historyTotal = historyItems.length;
    var historyLabel = document.getElementById("history-count-label");
    if (historyLabel) {
      historyLabel.textContent = historyVisible === historyTotal
        ? "(" + historyTotal + ")"
        : "(" + historyVisible + " av " + historyTotal + ")";
    }
    var historyEmpty = document.getElementById("history-filter-empty");
    if (historyEmpty) historyEmpty.hidden = !(historyTotal > 0 && historyVisible === 0);

    var newPanel = document.getElementById("new-panel");
    if (newPanel) {
      var newItems = newPanel.querySelectorAll("li.entry");
      var newVisible = 0;
      newItems.forEach(function (li) { if (li.style.display !== "none") newVisible++; });
      var newLabel = document.getElementById("new-count-label");
      if (newLabel) newLabel.textContent = newVisible;
      var newEmpty = document.getElementById("new-filter-empty");
      if (newEmpty) newEmpty.hidden = !(newItems.length > 0 && newVisible === 0);

      newPanel.querySelectorAll(".category-group").forEach(function (group) {
        var anyVisible = Array.prototype.some.call(
          group.querySelectorAll("li.entry"),
          function (li) { return li.style.display !== "none"; }
        );
        group.style.display = anyVisible ? "" : "none";
      });
    }
  }

  function applyFilter() {
    document.querySelectorAll("li.entry[data-source]").forEach(function (li) {
      var source = li.getAttribute("data-source");
      li.style.display = hiddenSources.has(source) ? "none" : "";
    });
    updateCounts();
  }

  document.querySelectorAll(".source-filter").forEach(function (checkbox) {
    checkbox.checked = !hiddenSources.has(checkbox.value);
    checkbox.addEventListener("change", function () {
      if (checkbox.checked) {
        hiddenSources.delete(checkbox.value);
      } else {
        hiddenSources.add(checkbox.value);
      }
      saveSet(STORAGE_HIDDEN, hiddenSources);
      applyFilter();
    });
  });

  applyReadState();
  applyFilter();
})();
"""
