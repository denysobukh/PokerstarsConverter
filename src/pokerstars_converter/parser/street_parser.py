from __future__ import annotations

import re
from dataclasses import dataclass, field

from pokerstars_converter.parser.action_parser import Action, _parse_single_action

# ── board card patterns ────────────────────────────────────────────────

# Flop:    *** ФЛОП *** [Jh 8s Qc]
_FLOP_BOARD_RE = re.compile(r'\*\*\*\s+ФЛОП\s+\*\*\*\s+\[([^\]]+)\]')

# Turn:    *** ТЕРН *** [Ah 3s 8c] [7s]
_TURN_BOARD_RE = re.compile(
    r'\*\*\*\s+ТЕРН\s+\*\*\*\s+\[[^\]]+\]\s+\[([^\]]+)\]'
)

# River:   *** РИВЕР *** [Ah 3s 8c 7s] [Jd]
_RIVER_BOARD_RE = re.compile(
    r'\*\*\*\s+РИВЕР\s+\*\*\*\s+\[[^\]]+\]\s+\[([^\]]+)\]'
)

# ── section boundaries ─────────────────────────────────────────────────

_FLOP_MARKER = "*** ФЛОП ***"
_TURN_MARKER = "*** ТЕРН ***"
_RIVER_MARKER = "*** РИВЕР ***"
_SHOWDOWN_MARKER = "*** ВСКРЫТИЕ КАРТ ***"
_SUMMARY_MARKER = "*** ИТОГ ***"


# ── data classes ───────────────────────────────────────────────────────


@dataclass
class BoardCards:
    """Board cards parsed from F/T/R markers."""
    flop: list[str] = field(default_factory=list)
    turn: str = ""
    river: str = ""


@dataclass
class StreetActions:
    """Actions parsed for each post-flop street."""
    flop: list[Action] = field(default_factory=list)
    turn: list[Action] = field(default_factory=list)
    river: list[Action] = field(default_factory=list)


@dataclass
class StreetData:
    """Complete post-preflop data: board + actions for each street."""
    board: BoardCards = field(default_factory=BoardCards)
    actions: StreetActions = field(default_factory=StreetActions)


# ── public API ─────────────────────────────────────────────────────────


def parse_streets(block: str) -> StreetData:
    """Parse board cards and actions for flop, turn, and river streets."""
    board = _parse_board_cards(block)
    actions = _parse_street_actions(block)
    return StreetData(board=board, actions=actions)


# ── board card extraction ─────────────────────────────────────────────


def _parse_board_cards(block: str) -> BoardCards:
    """Extract flop/turn/river cards from section markers."""
    flop_cards = _extract_flop_cards(block)
    turn_card = _extract_turn_card(block)
    river_card = _extract_river_card(block)
    return BoardCards(flop=flop_cards, turn=turn_card, river=river_card)


def _extract_flop_cards(block: str) -> list[str]:
    """Return flop cards from `*** ФЛОП *** [Jh 8s Qc]`."""
    for line in block.splitlines():
        m = _FLOP_BOARD_RE.search(line)
        if m:
            return _split_cards(m.group(1))
    return []


def _extract_turn_card(block: str) -> str:
    """Return the single turn card from `*** ТЕРН *** [...] [7s]`."""
    for line in block.splitlines():
        m = _TURN_BOARD_RE.search(line)
        if m:
            return m.group(1).strip()
    return ""


def _extract_river_card(block: str) -> str:
    """Return the single river card from `*** РИВЕР *** [...] [Jd]`."""
    for line in block.splitlines():
        m = _RIVER_BOARD_RE.search(line)
        if m:
            return m.group(1).strip()
    return ""


def _split_cards(raw: str) -> list[str]:
    """Split 'Jh 8s Qc' into ['Jh', '8s', 'Qc']."""
    return raw.split()


# ── street action extraction ──────────────────────────────────────────


def _parse_street_actions(block: str) -> StreetActions:
    """Parse actions for each post-flop street."""
    flop_lines = _extract_flop_action_lines(block)
    turn_lines = _extract_turn_action_lines(block)
    river_lines = _extract_river_action_lines(block)

    return StreetActions(
        flop=_actions_from_lines(flop_lines),
        turn=_actions_from_lines(turn_lines),
        river=_actions_from_lines(river_lines),
    )


def _extract_flop_action_lines(block: str) -> list[str]:
    """Lines between flop marker and turn/summary marker."""
    return _extract_section_lines(
        block, start=_FLOP_MARKER, stop_markers=[_TURN_MARKER, _SUMMARY_MARKER]
    )


def _extract_turn_action_lines(block: str) -> list[str]:
    """Lines between turn marker and river/summary/showdown marker."""
    return _extract_section_lines(
        block,
        start=_TURN_MARKER,
        stop_markers=[_RIVER_MARKER, _SHOWDOWN_MARKER, _SUMMARY_MARKER],
    )


def _extract_river_action_lines(block: str) -> list[str]:
    """Lines between river marker and showdown/summary marker."""
    return _extract_section_lines(
        block,
        start=_RIVER_MARKER,
        stop_markers=[_SHOWDOWN_MARKER, _SUMMARY_MARKER],
    )


def _extract_section_lines(
    block: str, start: str, stop_markers: list[str]
) -> list[str]:
    """Return action lines between *start* marker and any *stop_markers*."""
    lines = block.splitlines()
    in_section = False
    result: list[str] = []

    for line in lines:
        if start in line:
            in_section = True
            continue
        if in_section and any(marker in line for marker in stop_markers):
            break
        if in_section:
            result.append(line)

    return result


def _actions_from_lines(lines: list[str]) -> list[Action]:
    """Parse Action objects from raw lines, skipping non-action lines."""
    actions: list[Action] = []
    for line in lines:
        action = _parse_single_action(line)
        if action:
            actions.append(action)
    return actions
