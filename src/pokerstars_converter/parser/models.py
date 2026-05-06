from __future__ import annotations

from dataclasses import dataclass, field

from pokerstars_converter.parser.action_parser import Action
from pokerstars_converter.parser.header_parser import HandHeader
from pokerstars_converter.parser.showdown_parser import ShowdownData
from pokerstars_converter.parser.street_parser import StreetData


@dataclass
class Hand:
    """Aggregated parsed data for a single poker hand."""
    header: HandHeader
    hero_name: str
    hero_cards: str
    hero_position: str
    eff_stack_bb: int
    villain_positions: list[str]
    position_map: dict[str, str]
    preflop_actions: list[Action] = field(default_factory=list)
    street_data: StreetData | None = None
    showdown: ShowdownData | None = None
