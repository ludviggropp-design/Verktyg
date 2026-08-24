"""Gemensamma hjälpfunktioner för källorna."""

from __future__ import annotations


def contains_term(text: str, term: str) -> bool:
    """Skiftlägesokänslig kontroll om `term` finns i `text`.

    Används som ett extra säkerhetsfilter utöver källornas egna sökfrågor,
    så att vi aldrig rapporterar träffar som faktiskt inte nämner ordet.
    """
    if not text or not term:
        return False
    return term.strip().lower() in text.lower()
