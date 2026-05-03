import re

HAND_SEPARATOR_RE = re.compile(r'\*{7,}\s+№\d+\s+\*{7,}')


def split_hands(text: str) -> list[str]:
    """Split a PokerStars export into individual hand blocks."""
    parts = HAND_SEPARATOR_RE.split(text)
    result: list[str] = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        if not _is_hand_block(stripped):
            continue
        result.append(stripped)
    return result


def _is_hand_block(text: str) -> bool:
    """Return True if *text* looks like the start of a hand record."""
    return bool(re.match(r'Раздача\s+PokerStars\s+№', text))
