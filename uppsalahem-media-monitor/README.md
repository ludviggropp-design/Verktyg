# Uppsalahem – omvärldsbevakare

Ett fristående Python-verktyg som bevakar när **Uppsalahem** nämns i:

- **Redaktionellt material** – dels brett via Google News och Bing News,
  dels riktat mot lokala Uppsala-medier: **SVT Nyheter Uppsala** och
  **Sveriges Radio P4 Uppland** (SR Uppland).
- **Sociala medier** – via publika sök-API:er som inte kräver egna nycklar:
  Reddit och Bluesky.

Verktyget körs manuellt eller schemalagt (t.ex. via cron). Varje körning
hämtar aktuella träffar, filtrerar fram de som faktiskt nämner sökordet,
och rapporterar bara de som är **nya** sedan förra körningen. All historik
sparas lokalt så inget krävs utöver filsystemet.

## Snabbstart på Windows (ingen terminal krävs)

1. Installera Python från [python.org/downloads](https://www.python.org/downloads/)
   – kryssa i "Add python.exe to PATH" i installationsfönstret.
2. Packa upp den här mappen (om du fått den som zip).
3. Dubbelklicka på **`Kör bevakaren.bat`**.

Första gången tar det en liten stund extra (den förbereder verktyget).
Varje gång öppnas resultatet automatiskt som en webbsida,
`data/report.html`, i din vanliga webbläsare – ingen kommandorad behövs
för den löpande användningen. En fullständig, bebilderad
steg-för-steg-guide finns separat om du vill ha mer stöd.

## Installation (Mac/Linux, eller manuellt på Windows)

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
python -m monitor.main --sources google_news,bing_news,svt_uppsala,sr_uppland

# Maskinläsbar output (t.ex. för att skicka vidare till Slack/e-post själv)
python -m monitor.main --json

# Se alla aktuella träffar, inte bara nya sedan sist
python -m monitor.main --include-seen

# Hoppa över att skriva den lokala HTML-rapporten (t.ex. vid schemaläggning)
python -m monitor.main --no-html
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
- `report.html` – en läsbar webbsida med senaste körningens nya träffar
  längst upp och hela historiken därunder. Skrivs om vid varje körning
  om inte `--no-html` anges. Öppna filen direkt i webbläsaren, eller
  låt `Kör bevakaren.bat` göra det åt dig. Sidan har egna kontroller
  (källfilter, viktningsfilter, sortering) och egen viktning/läst-status
  som sparas i webbläsarens localStorage, inte i den här filen – se
  "Vikta och filtrera i rapporten" nedan.

## Källor

| Namn (`--sources`) | Typ | Vad det är |
| --- | --- | --- |
| `google_news` | redaktionellt | Google News RSS, sökning på sökordet över alla svenska nyhetssajter Google indexerar. |
| `bing_news` | redaktionellt | Bing News RSS, samma princip som Google News men ett annat sökindex – ett bra komplement, fångar ibland andra träffar. |
| `svt_uppsala` | redaktionellt | SVT Nyheter Uppsalas lokala nyhetsflöde. Fast URL (inget sökord i själva flödet) – filtreras på sökordet i titel/beskrivning. |
| `sr_uppland` | redaktionellt | Sveriges Radios öppna RSS-API för P4 Uppland (programid 114). Samma princip: fast flöde, filtreras på sökordet. Eftersom det är radioavsnitt hittas bara det som syns i avsnittens text (titel/beskrivning), inte allt som sägs i sändning. |
| `reddit` | socialt | Reddits publika sök-API. |
| `bluesky` | socialt | Blueskys publika sök-API (AT Protocol). |

Alla RSS-baserade källor (`google_news`, `bing_news`, `svt_uppsala`,
`sr_uppland`) delar samma hämtnings- och parsningslogik i
`monitor/sources/rss_utils.py`.

**Om UNT (Upsala Nya Tidning):** UNT har egna RSS-flöden, men den exakta
adressen kunde inte bekräftas härifrån (nätverksspärr mot unt.se i den
här utvecklingsmiljön). Vill ni ha UNT som källa: öppna
[UNT:s RSS-sida](https://www.unt.se/kundinfo/artikel/har-ar-vara-rss-floden-som-du-kan-folja/kr2n78pr),
hitta rätt flödesadress där, så lägger vi till den som en riktad källa
precis som SVT Uppsala och SR Uppland.

**Om X/Twitter, Facebook och Instagram:** kräver betal-API:er för sök och
är därför inte inkluderade som standard – de kan läggas till på samma sätt
som övriga källor om/när ni skaffar API-nycklar.

## Vikta och filtrera i rapporten

I `report.html` kan varje artikel märkas **positiv (grön), neutral (gul)**
eller **negativ (röd)** genom att klicka på en av de tre små runda
knapparna uppe till höger på artikeln. Ett nytt klick på samma vikt tar
bort den igen. Den valda vikten syns både som en ifylld knapp och som en
färgad kant till vänster om artikeln, så det går att skumma listan snabbt.

Kontrollraden högst upp på sidan låter er:

- **Visa källor** – bocka ur en källa för att dölja den överallt på sidan.
- **Visa vikt** – visa bara t.ex. bara de negativa träffarna, eller dölja
  allt som redan är viktat.
- **Sortera efter** – publiceringsdatum eller upptäcktsdatum, i valfri
  riktning.

Allt detta (viktning, filterval, sorteringsval, lästa artiklar) sparas i
webbläsarens `localStorage` och gäller alltså den specifika datorn/
webbläsaren, inte filen `report.html` i sig – kör ni verktyget på flera
datorer förs inte viktningen över mellan dem.

## Schemaläggning (cron)

Kör t.ex. varje timme och skicka utskriften till en loggfil:

```cron
0 * * * * cd /path/till/uppsalahem-media-monitor && .venv/bin/python -m monitor.main --no-html >> monitor.log 2>&1
```

(`--no-html` är valfritt men praktiskt på en server utan webbläsare – utan
flaggan skrivs `data/report.html` om vid varje körning ändå.)

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

## Tester

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Testerna mockar alla nätverksanrop, så de kör utan internetuppkoppling.
