# Uppsalahem – omvärldsbevakare

Ett fristående Python-verktyg som bevakar när **Uppsalahem** nämns i:

- **Redaktionellt material** – nyheter och press, via Google News RSS.
- **Sociala medier** – via publika sök-API:er som inte kräver egna nycklar:
  Reddit och Bluesky.

Verktyget körs manuellt eller schemalagt (t.ex. via cron). Varje körning
hämtar aktuella träffar, filtrerar fram de som faktiskt nämner sökordet,
och rapporterar bara de som är **nya** sedan förra körningen. All historik
sparas lokalt så inget krävs utöver filsystemet.

## Installation

```bash
cd uppsalahem-media-monitor
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Användning

```bash
# Kör med standardinställningar (alla källor, sökord "Uppsalahem")
python -m monitor.main

# Ange eget sökord
python -m monitor.main --search-term "Uppsalahem AB"

# Bevaka bara vissa källor
python -m monitor.main --sources google_news,reddit

# Maskinläsbar output (t.ex. för att skicka vidare till Slack/e-post själv)
python -m monitor.main --json

# Se alla aktuella träffar, inte bara nya sedan sist
python -m monitor.main --include-seen
```

Vid varje körning:

1. Hämtas träffar från de aktiva källorna.
2. Träffar som inte faktiskt innehåller sökordet i titel/text filtreras bort
   (extra säkerhetsfilter utöver källornas egna sökfrågor).
3. Träffar som redan rapporterats tidigare filtreras bort (deduplicering).
4. Nya träffar skrivs ut och läggs till i historikloggen.
5. Tillståndet (vilka träffar som är "sedda") sparas.

## Data som sparas

I `data/`-katalogen (skapas automatiskt, ligger utanför git):

- `seen.json` – id:n för alla träffar som redan rapporterats, för
  deduplicering mellan körningar.
- `log.jsonl` – en logg-rad per ny träff som någonsin hittats, med
  tidsstämpel för när den upptäcktes. Bra underlag för statistik eller
  export till t.ex. ett kalkylark.

## Schemaläggning (cron)

Kör t.ex. varje timme och skicka utskriften till en loggfil:

```cron
0 * * * * cd /path/till/uppsalahem-media-monitor && .venv/bin/python -m monitor.main >> monitor.log 2>&1
```

Vill du bara agera på nya träffar (t.ex. skicka notis) kan du kombinera med
`--json` och ett eget litet skript/one-liner som läser stdout och postar
till Slack, e-post eller liknande – `monitor.main.run()` returnerar redan
en ren lista av nya träffar om du hellre importerar och anropar det direkt
från Python.

## Lägga till fler källor

Varje källa är en funktion `fetch(search_term: str) -> list[Mention]` i
`monitor/sources/`. Lägg till en ny fil, implementera `fetch`, och
registrera den i `monitor/sources/__init__.py`:s `SOURCE_REGISTRY`.
Sätt `category` till `"redaktionellt"` eller `"socialt"` beroende på typ
av källa.

X/Twitter, Facebook och Instagram kräver betal-API:er för sök och är
därför inte inkluderade som standard – de kan läggas till på samma sätt
om/när ni skaffar API-nycklar.

## Tester

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Testerna mockar alla nätverksanrop, så de kör utan internetuppkoppling.
