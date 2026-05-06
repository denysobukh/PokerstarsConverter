from __future__ import annotations

from pokerstars_converter.parser.action_parser import Action
from pokerstars_converter.parser.models import Hand
from pokerstars_converter.utils.betsize import quantize_size

_ACTION_SYMBOLS = {
    "fold": "f",
    "check": "x",
    "call": "c",
    "bet": "b",
    "raise": "r",
}


def format_hand(hand: Hand, hand_number: int) -> str:
    """Assemble a parsed Hand into the compact notation string."""
    lines = [
        f"Hand#{hand_number}",
        f"{hand.hero_cards} {hand.hero_position} {hand.eff_stack_bb}bb vs {', '.join(hand.villain_positions)}",
        "",
    ]

    # Preflop
    pf_str = _format_actions(hand.preflop_actions, hand.position_map, hand.header.bb, hand.eff_stack_bb)
    if pf_str:
        lines.append(f"PF: {pf_str}")

    # Postflop streets
    has_postflop = False
    if hand.street_data:
        sd = hand.street_data
        if sd.board.flop:
            flop_str = _format_actions(sd.actions.flop, hand.position_map, hand.header.bb, hand.eff_stack_bb)
            lines.append(f"F {''.join(sd.board.flop)}: {flop_str}")
            has_postflop = True
        if sd.board.turn:
            turn_str = _format_actions(sd.actions.turn, hand.position_map, hand.header.bb, hand.eff_stack_bb)
            lines.append(f"T {sd.board.turn}: {turn_str}")
            has_postflop = True
        if sd.board.river:
            river_str = _format_actions(sd.actions.river, hand.position_map, hand.header.bb, hand.eff_stack_bb)
            lines.append(f"R {sd.board.river}: {river_str}")
            has_postflop = True

    # Showdown (only if cards were shown)
    if has_postflop and hand.showdown and hand.showdown.villains:
        lines.append("")

    if hand.showdown and hand.showdown.villains:
        for v in hand.showdown.villains:
            pos = hand.position_map.get(v.player, "UNKNOWN")
            lines.append(f"SD: {pos} {''.join(v.cards)} = {v.hand_name}")

    # Result
    result = hand.showdown.result if hand.showdown else "unknown"
    lines.append(f"Result: {result}")

    return "\n".join(lines)


def _format_actions(actions: list[Action], pos_map: dict[str, str], bb: float, eff_bb: int) -> str:
    """Convert a list of Actions into a single street notation string."""
    parts = []
    for act in actions:
        pos = pos_map.get(act.player, "UNKNOWN")

        # All-in is only explicit for voluntary aggression (bet/raise)
        if act.all_in and act.action_type in ("bet", "raise"):
            sym = "a"
            size_str = quantize_size(act.amount, 0.0, bb, eff_bb, is_all_in=True)
        elif act.action_type in _ACTION_SYMBOLS:
            sym = _ACTION_SYMBOLS[act.action_type]
            if act.action_type in ("bet", "raise"):
                size_str = quantize_size(act.amount, 0.0, bb, eff_bb)
            else:
                size_str = ""
        else:
            sym = "?"
            size_str = ""

        if size_str:
            parts.append(f"{pos} {sym} {size_str}")
        else:
            parts.append(f"{pos} {sym}")

    return " / ".join(parts)
