from __future__ import annotations

import sys
from pathlib import Path

from pokerstars_converter.parser.hand_splitter import split_hands
from pokerstars_converter.parser.header_parser import parse_header
from pokerstars_converter.parser.hero_parser import extract_hero, format_hero_cards
from pokerstars_converter.parser.position_mapper import assign_positions
from pokerstars_converter.parser.action_parser import parse_preflop_actions
from pokerstars_converter.parser.street_parser import parse_streets
from pokerstars_converter.parser.showdown_parser import parse_showdown
from pokerstars_converter.parser.models import Hand
from pokerstars_converter.utils.stacks import compute_eff_stack_bb
from pokerstars_converter.utils.villains import compute_villains
from pokerstars_converter.formatter import format_hand


def parse_hand(block: str) -> Hand | None:
    """Parse a single hand block into a Hand object.
    
    Returns None if Hero is not present in the hand.
    """
    header = parse_header(block)
    hero_info = extract_hero(block)
    if not hero_info:
        return None

    hero_name = hero_info.name
    hero_cards = format_hero_cards(hero_info.card1, hero_info.card2)

    active_seats = sorted(header.seats.keys())
    seat_to_pos = assign_positions(header.button_seat, active_seats)
    name_to_pos = {info.name: seat_to_pos[info.seat_number] for info in header.seats.values()}
    hero_pos = name_to_pos.get(hero_name, "UNKNOWN")

    pf_data = parse_preflop_actions(block)
    pf_actions = pf_data.actions

    villain_positions = compute_villains(pf_actions, hero_name, name_to_pos)

    hero_chips = next((info.stack for info in header.seats.values() if info.name == hero_name), 0.0)
    villain_chips = [
        info.stack for info in header.seats.values()
        if info.name != hero_name and name_to_pos.get(info.name) in villain_positions
    ]
    eff_bb = compute_eff_stack_bb(hero_chips, villain_chips, header.bb)

    street_data = parse_streets(block)
    showdown = parse_showdown(block, hero_name)

    return Hand(
        header=header,
        hero_name=hero_name,
        hero_cards=hero_cards,
        hero_position=hero_pos,
        eff_stack_bb=eff_bb,
        villain_positions=villain_positions,
        position_map=name_to_pos,
        preflop_actions=pf_actions,
        street_data=street_data,
        showdown=showdown,
    )


def main():
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: File '{sys.argv[1]}' not found.", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        command = Path(sys.argv[0]).name or "pokerstars-converter"
        if command == "converter.py":
            command = "python converter.py"
        print(f"Usage: {command} <input_file.txt>", file=sys.stderr)
        print(f"   or: {command} < input_file.txt", file=sys.stderr)
        print(f"   or: pbpaste | {command}", file=sys.stderr)
        sys.exit(1)

    raw_hands = split_hands(text)
    hand_number = 0
    outputs = []

    for block in raw_hands:
        hand = parse_hand(block)
        if hand is None:
            continue
        hand_number += 1
        outputs.append(format_hand(hand, hand_number))

    print("\n\n".join(outputs))


if __name__ == "__main__":
    main()
