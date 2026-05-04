from __future__ import annotations

from parser.action_parser import Action


def compute_villains(
    actions: list[Action],
    hero_name: str,
    positions: dict[str, str],
) -> list[str]:
    """Determine villain positions for the header line.

    *actions* — ordered list of preflop actions.
    *hero_name* — the hero's player name.
    *positions* — mapping from player name to position label
                  (e.g. ``{"Hero": "CO", "Villain1": "SB"}``).

    Returns a list of position labels for villains who:
    - did not fold before Hero acted preflop, AND
    - voluntarily put chips in the pot while Hero was still active.

    When Hero folds immediately (first legal action), only SB and BB
    are listed (if present).
    """
    if not actions:
        return []

    hero_first_idx = _hero_first_action_index(actions, hero_name)

    # Hero folds immediately → list only blinds
    if _hero_folded_immediately(actions, hero_name, hero_first_idx):
        return _list_blinds(positions)

    # Collect players who folded before Hero acted
    folded_before_hero: set[str] = set()
    for i in range(hero_first_idx):
        a = actions[i]
        if a.action_type == "fold" and a.player != hero_name:
            folded_before_hero.add(a.player)

    # Collect villains who voluntarily put chips in while Hero active
    villains: set[str] = set()
    for a in actions[hero_first_idx:]:
        if a.player == hero_name:
            continue
        if a.player in folded_before_hero:
            continue
        if a.action_type in ("call", "raise", "bet"):
            villains.add(a.player)

    # Map villain names to position labels
    result: list[str] = []
    for name in villains:
        pos = positions.get(name)
        if pos:
            result.append(pos)

    return result


# ── helpers ────────────────────────────────────────────────────────────


def _hero_first_action_index(
    actions: list[Action],
    hero_name: str,
) -> int:
    """Return the index of Hero's first action, or len(actions) if none."""
    for i, a in enumerate(actions):
        if a.player == hero_name:
            return i
    return len(actions)


def _hero_folded_immediately(
    actions: list[Action],
    hero_name: str,
    hero_first_idx: int,
) -> bool:
    """True when Hero's first legal action is a fold."""
    if hero_first_idx >= len(actions):
        return False
    return actions[hero_first_idx].action_type == "fold"


def _list_blinds(positions: dict[str, str]) -> list[str]:
    """Return SB and BB positions (in that order) if present."""
    blinds: list[str] = []
    for pos_label in ("SB", "BB"):
        # Find the player name that maps to this position
        for name, pos in positions.items():
            if pos == pos_label:
                blinds.append(pos_label)
                break
    return blinds
