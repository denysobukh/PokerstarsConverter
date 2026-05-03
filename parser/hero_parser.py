from __future__ import annotations

import re
from dataclasses import dataclass

# Line: Карты PlayerName [rank1suit rank2suit]
_HOLE_CARDS_RE = re.compile(r'Карты\s+(\S+)\s+\[([^\]]+)\]')

# Individual card: rank + suit, e.g. "Ad", "Ts", "9c"
_CARD_RE = re.compile(r'^([AKQJT2-9]+)([cdhs])$')


@dataclass
class HeroInfo:
    name: str
    card1: str
    card2: str


def extract_hero(block: str) -> HeroInfo | None:
    """Return HeroInfo from the first `Карты` line in the preflop section,
    or None if no hero cards are found."""
    for line in block.splitlines():
        m = _HOLE_CARDS_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        raw_cards = m.group(2)
        card1, card2 = _parse_two_cards(raw_cards)
        if card1 and card2:
            return HeroInfo(name=name, card1=card1, card2=card2)
    return None


# ── card helpers ───────────────────────────────────────────────────────


def _parse_two_cards(raw: str) -> tuple[str, str]:
    """Split 'Ad Td' into ('Ad', 'Td') – validates each token."""
    tokens = raw.split()
    if len(tokens) != 2:
        return ('', '')
    c1 = _normalize_card(tokens[0])
    c2 = _normalize_card(tokens[1])
    return (c1, c2)


def _normalize_card(token: str) -> str:
    """Return the token unchanged if it matches rank+suit, else empty."""
    m = _CARD_RE.match(token)
    return m.group(0) if m else ''


def card_rank(card: str) -> str:
    """Return the rank part of a card string, e.g. 'Ad' -> 'A'."""
    m = _CARD_RE.match(card)
    return m.group(1) if m else ''


def card_suit(card: str) -> str:
    """Return the suit part of a card string, e.g. 'Ad' -> 'd'."""
    m = _CARD_RE.match(card)
    return m.group(2) if m else ''


def format_hero_cards(card1: str, card2: str) -> str:
    """Format two cards for output notation.

    Rules:
    - Pocket pair  -> full cards with suits, e.g. 'AdTd' or 'AhKh'
    - Non-pair    -> full cards with suits, e.g. 'AdTd' or 'AhKh'
    """
    r1 = card_rank(card1)
    r2 = card_rank(card2)
    return card1 + card2
