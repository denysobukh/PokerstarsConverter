from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── showdown card line ─────────────────────────────────────────────────
# "PlayerName: открывает [Th 9h] (стрит [семерка - валет])"
# "PlayerName: открывает [Jd 9d] (старшую карту [туз])"
_SHOWDOWN_CARDS_RE = re.compile(
    r'^(\S+):\s+открывает\s+\[([^\]]+)\]\s+\(([^)]+)\)'
)

# ── summary result lines ───────────────────────────────────────────────
# "Место 1: Avviee открыл [Ad Td] и проиграл , собрав пару [тузы]"
# "Место 3: jonnyjm (малый блайнд) открыл [Th 9h] и выиграл ($3.06) , ..."
# "Место 1: Avviee (баттон) сделал фолд до Флоп (не ставил)"
# "Место 1: Avviee (малый блайнд) собрал ($0.04)"
_SUMMARY_WIN_RE = re.compile(r'(\S+)\s+.*?\s+и выиграл')
_SUMMARY_LOSE_RE = re.compile(r'(\S+)\s+.*?\s+и проиграл')
_SUMMARY_FOLD_RE = re.compile(r'(\S+)\s+.*?\s+сделал фолд')
_SUMMARY_COLLECTED_RE = re.compile(r'(\S+)\s+.*?\s+собрал\s+\(')

# ── section markers ────────────────────────────────────────────────────
_SHOWDOWN_MARKER = "*** ВСКРЫТИЕ КАРТ ***"
_SUMMARY_MARKER = "*** ИТОГ ***"

# ── Russian → English hand-name mapping ────────────────────────────────
_HAND_NAME_MAP: list[tuple[str, str]] = [
    ("стрит-флеш", "straight flush"),
    ("роял-флеш", "royal flush"),
    ("старшую карту", "high card"),
    ("пару", "pair"),
    ("две пары", "two pair"),
    ("тройку", "set"),
    ("стрит", "straight"),
    ("флеш", "flush"),
    ("фулл-хаус", "full house"),
    ("каретку", "quads"),
]


# ── data classes ───────────────────────────────────────────────────────


@dataclass
class ShowdownVillain:
    """A single villain's showdown information."""
    player: str
    cards: list[str]
    hand_name: str


@dataclass
class ShowdownData:
    """Parsed showdown and result data for a hand.

    When there is no showdown marker and the hero did not fold,
    the caller should treat the return value as None (handled by
    the public API).
    """
    villains: list[ShowdownVillain] = field(default_factory=list)
    result: str = "unknown"  # "won" | "lost" | "fold" | "unknown"


# ── public API ─────────────────────────────────────────────────────────


def parse_showdown(block: str, hero_name: str) -> ShowdownData | None:
    """Parse showdown cards, hand names, and win/loss/fold outcome.

    Returns None when there is no showdown *and* the hero did not fold
    (e.g. hand ended with all villains folding before showdown).
    """
    lines = block.splitlines()
    has_showdown_marker = any(_SHOWDOWN_MARKER in l for l in lines)

    villains = _parse_showdown_villains(block, hero_name) if has_showdown_marker else []
    result = _parse_result(block, hero_name)

    if not has_showdown_marker and result != "fold":
        return None

    return ShowdownData(villains=villains, result=result)


# ── showdown villain parsing ───────────────────────────────────────────


def _parse_showdown_villains(block: str, hero_name: str) -> list[ShowdownVillain]:
    """Extract each villain's shown cards and hand name from the
    *** ВСКРЫТИЕ КАРТ *** section."""
    villains: list[ShowdownVillain] = []
    in_showdown = False

    for line in block.splitlines():
        if _SHOWDOWN_MARKER in line:
            in_showdown = True
            continue
        if not in_showdown:
            continue
        if _SUMMARY_MARKER in line:
            break
        m = _SHOWDOWN_CARDS_RE.match(line)
        if m:
            player = m.group(1)
            if player == hero_name:
                continue
            cards = m.group(2).split()
            hand_name_raw = m.group(3)
            hand_name = _translate_hand_name(hand_name_raw)
            villains.append(
                ShowdownVillain(
                    player=player,
                    cards=cards,
                    hand_name=hand_name,
                )
            )
    return villains


def _translate_hand_name(raw: str) -> str:
    """Map a Russian hand-name fragment to its English equivalent.

    The raw string may contain extra detail after the first word/phrase,
    e.g. 'стрит [семерка - валет]' or 'пару [тузы]'.  We match against
    known prefixes.
    """
    for ru_key, en_value in _HAND_NAME_MAP:
        if raw.startswith(ru_key):
            return en_value
    return "unknown"


# ── result parsing ─────────────────────────────────────────────────────


def _parse_result(block: str, hero_name: str) -> str:
    """Determine hero's outcome from the *** ИТОГ *** section."""
    in_summary = False

    for line in block.splitlines():
        if _SUMMARY_MARKER in line:
            in_summary = True
            continue
        if not in_summary:
            continue
        if _is_hero_result_line(line, hero_name):
            if _SUMMARY_WIN_RE.search(line):
                return "won"
            if _SUMMARY_LOSE_RE.search(line):
                return "lost"
            if _SUMMARY_FOLD_RE.search(line):
                return "fold"
            if _SUMMARY_COLLECTED_RE.search(line):
                return "won"
    return "unknown"


def _is_hero_result_line(line: str, hero_name: str) -> bool:
    """Check whether a summary line belongs to the hero.

    Summary lines start with 'Место N:' followed by the player name
    (optionally with a position in parentheses).
    """
    # Strip the 'Место N:' prefix
    m = re.match(r'Место\s+\d+:\s+', line)
    if not m:
        return False
    remainder = line[m.end():]
    # Player name is the first token (before optional '(')
    name_match = re.match(r'(\S+)', remainder)
    if not name_match:
        return False
    return name_match.group(1) == hero_name
