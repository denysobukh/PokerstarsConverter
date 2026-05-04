from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── action line patterns ───────────────────────────────────────────────

# "PlayerName: делает фолд"
_FOLD_RE = re.compile(r'^(\S+):\s+делает фолд$')

# "PlayerName: делает чек"
_CHECK_RE = re.compile(r'^(\S+):\s+делает чек$')

# "PlayerName: делает колл $X"
_CALL_RE = re.compile(r'^(\S+):\s+делает колл \$([0-9.]+)$')

# "PlayerName: делает колл $X и олл-ин"
_CALL_ALLIN_RE = re.compile(r'^(\S+):\s+делает колл \$([0-9.]+)\s+и олл-ин$')

# "PlayerName: делает рейз $X $Y"
_RAISE_RE = re.compile(r'^(\S+):\s+делает рейз \$([0-9.]+)\s+\$([0-9.]+)$')

# "PlayerName: делает рейз $X $Y и олл-ин"
_RAISE_ALLIN_RE = re.compile(
    r'^(\S+):\s+делает рейз \$([0-9.]+)\s+\$([0-9.]+)\s+и олл-ин$'
)

# "PlayerName: делает бет $X"
_BET_RE = re.compile(r'^(\S+):\s+делает бет \$([0-9.]+)$')

# "PlayerName: делает бет $X и олл-ин"
_BET_ALLIN_RE = re.compile(r'^(\S+):\s+делает бет \$([0-9.]+)\s+и олл-ин$')

# ── section boundaries ─────────────────────────────────────────────────

_PREFLOP_START = "*** ЗАКРЫТЫЕ КАРТЫ ***"
_FLOP_START = "*** ФЛОП ***"


@dataclass
class Action:
    """A single parsed player action."""
    player: str
    action_type: str  # "fold", "call", "raise", "bet", "check"
    amount: float = 0.0
    all_in: bool = False


@dataclass
class PreflopActions:
    """All parsed preflop actions for a hand block."""
    actions: list[Action] = field(default_factory=list)


def extract_preflop_section(block: str) -> str:
    """Return only the lines between the preflop marker and the flop marker
    (or end of block if no flop)."""
    lines = block.splitlines()
    in_section = False
    section_lines: list[str] = []

    for line in lines:
        if _PREFLOP_START in line:
            in_section = True
            continue
        if _FLOP_START in line:
            break
        if in_section:
            section_lines.append(line)

    return "\n".join(section_lines)


def parse_preflop_actions(block: str) -> PreflopActions:
    """Parse all player actions in the preflop section of a hand block."""
    section = extract_preflop_section(block)
    actions: list[Action] = []

    for line in section.splitlines():
        action = _parse_single_action(line)
        if action:
            actions.append(action)

    return PreflopActions(actions=actions)


# ── single-line parser ─────────────────────────────────────────────────


def _parse_single_action(line: str) -> Action | None:
    """Try to parse one action line.  Returns None for non-action lines."""
    for pattern, handler in [
        (_FOLD_RE, _handle_fold),
        (_CHECK_RE, _handle_check),
        (_CALL_ALLIN_RE, _handle_call_allin),
        (_CALL_RE, _handle_call),
        (_RAISE_ALLIN_RE, _handle_raise_allin),
        (_RAISE_RE, _handle_raise),
        (_BET_ALLIN_RE, _handle_bet_allin),
        (_BET_RE, _handle_bet),
    ]:
        m = pattern.match(line)
        if m:
            return handler(m)
    return None


def _handle_fold(m: re.Match) -> Action:
    return Action(player=m.group(1), action_type="fold")


def _handle_check(m: re.Match) -> Action:
    return Action(player=m.group(1), action_type="check")


def _handle_call(m: re.Match) -> Action:
    return Action(player=m.group(1), action_type="call", amount=float(m.group(2)))


def _handle_call_allin(m: re.Match) -> Action:
    return Action(
        player=m.group(1), action_type="call", amount=float(m.group(2)), all_in=True
    )


def _handle_raise(m: re.Match) -> Action:
    # m.group(3) is the total bet amount (second dollar figure)
    return Action(player=m.group(1), action_type="raise", amount=float(m.group(3)))


def _handle_raise_allin(m: re.Match) -> Action:
    return Action(
        player=m.group(1), action_type="raise", amount=float(m.group(3)), all_in=True
    )


def _handle_bet(m: re.Match) -> Action:
    return Action(player=m.group(1), action_type="bet", amount=float(m.group(2)))


def _handle_bet_allin(m: re.Match) -> Action:
    return Action(
        player=m.group(1), action_type="bet", amount=float(m.group(2)), all_in=True
    )
