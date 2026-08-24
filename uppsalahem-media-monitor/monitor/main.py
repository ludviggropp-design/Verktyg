"""CLI-ingång för Uppsalahems omvärldsbevakare.

Körexempel:
    python -m monitor.main
    python -m monitor.main --search-term "Uppsalahem" --sources google_news,reddit
    python -m monitor.main --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import DEFAULT_DATA_DIR, DEFAULT_SEARCH_TERM, DEFAULT_SOURCES
from .models import Mention
from .sources import SOURCE_REGISTRY
from .state import State


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Omvärldsbevakare för Uppsalahem.")
    parser.add_argument(
        "--search-term",
        default=DEFAULT_SEARCH_TERM,
        help=f"Sökord att bevaka (standard: {DEFAULT_SEARCH_TERM!r}).",
    )
    parser.add_argument(
        "--sources",
        default=",".join(DEFAULT_SOURCES),
        help=(
            "Kommaseparerad lista av källor att bevaka. Tillgängliga: "
            f"{', '.join(SOURCE_REGISTRY)} (standard: alla)."
        ),
    )
    parser.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        help="Katalog där tillstånd (sedda träffar) och logg sparas.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Skriv ut nya träffar som JSON istället för läsbar text.",
    )
    parser.add_argument(
        "--include-seen",
        action="store_true",
        help="Visa alla träffar från källorna, inte bara nya sedan förra körningen.",
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> list[Mention]:
    source_names = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in source_names if s not in SOURCE_REGISTRY]
    if unknown:
        raise SystemExit(
            f"Okänd(a) källa/källor: {', '.join(unknown)}. "
            f"Tillgängliga: {', '.join(SOURCE_REGISTRY)}"
        )

    state = State(Path(args.data_dir))
    all_mentions: list[Mention] = []

    for name in source_names:
        fetch_fn = SOURCE_REGISTRY[name]
        try:
            mentions = fetch_fn(args.search_term)
        except Exception as exc:  # nätverksfel från en källa ska inte stoppa övriga
            print(f"[varning] kunde inte hämta från '{name}': {exc}", file=sys.stderr)
            continue
        all_mentions.extend(mentions)

    if args.include_seen:
        new_mentions = all_mentions
    else:
        new_mentions = [m for m in all_mentions if state.is_new(m)]

    state.mark_seen(all_mentions)
    state.append_log(new_mentions)
    state.save()

    return new_mentions


def report(mentions: list[Mention], as_json: bool) -> None:
    if as_json:
        print(json.dumps([m.to_dict() for m in mentions], ensure_ascii=False, indent=2))
        return

    if not mentions:
        print("Inga nya nämningar av Uppsalahem hittades.")
        return

    print(f"{len(mentions)} ny(a) nämning(ar) av Uppsalahem:\n")
    by_category: dict[str, list[Mention]] = {}
    for m in mentions:
        by_category.setdefault(m.category, []).append(m)

    for category, items in by_category.items():
        print(f"== {category.upper()} ==")
        for m in items:
            print(f"- [{m.source}] {m.title}")
            if m.author:
                print(f"    Av: {m.author}")
            if m.published_at:
                print(f"    Publicerad: {m.published_at}")
            print(f"    {m.url}")
        print()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mentions = run(args)
    report(mentions, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
