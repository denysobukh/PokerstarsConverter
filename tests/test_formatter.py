import pytest

from pokerstars_converter.parser.action_parser import Action
from pokerstars_converter.parser.header_parser import HandHeader, SeatInfo
from pokerstars_converter.parser.models import Hand
from pokerstars_converter.parser.showdown_parser import ShowdownData, ShowdownVillain
from pokerstars_converter.parser.street_parser import BoardCards, StreetActions, StreetData
from pokerstars_converter.formatter import format_hand


@pytest.fixture
def base_hand():
    """Create a minimal Hand object for testing."""
    header = HandHeader(
        sb=0.01,
        bb=0.02,
        button_seat=1,
        seats={
            1: SeatInfo(seat_number=1, name="Hero", stack=2.0),
            2: SeatInfo(seat_number=2, name="Villain", stack=2.0),
        },
    )
    return Hand(
        header=header,
        hero_name="Hero",
        hero_cards="AdTd",
        hero_position="BU",
        eff_stack_bb=100,
        villain_positions=["BB"],
        position_map={"Hero": "BU", "Villain": "BB"},
    )


class TestHeaderFormatting:
    def test_basic_header(self, base_hand):
        out = format_hand(base_hand, 1)
        assert "Hand#1" in out
        assert "AdTd BU 100bb vs BB" in out

    def test_multiple_villains(self, base_hand):
        base_hand.villain_positions = ["SB", "BB", "UTG"]
        out = format_hand(base_hand, 5)
        assert "Hand#5" in out
        assert "vs SB, BB, UTG" in out


class TestPreflopFormatting:
    def test_fold_only(self, base_hand):
        base_hand.preflop_actions = [Action("Hero", "fold")]
        base_hand.showdown = ShowdownData(result="fold")
        out = format_hand(base_hand, 1)
        assert "PF: BU f" in out
        assert "Result: fold" in out

    def test_raise_and_call(self, base_hand):
        base_hand.preflop_actions = [
            Action("Hero", "raise", amount=0.04),
            Action("Villain", "call", amount=0.04),
        ]
        out = format_hand(base_hand, 2)
        assert "PF: BU r 2.0bb / BB c" in out

    def test_bb_checks_option(self, base_hand):
        base_hand.preflop_actions = [Action("Villain", "check")]
        out = format_hand(base_hand, 3)
        assert "PF: BB x" in out


class TestPostflopFormatting:
    def test_flop_only(self, base_hand):
        base_hand.street_data = StreetData(
            board=BoardCards(flop=["Ah", "3s", "8c"]),
            actions=StreetActions(
                flop=[Action("Villain", "bet", amount=0.03), Action("Hero", "call", amount=0.03)]
            ),
        )
        out = format_hand(base_hand, 4)
        assert "F Ah3s8c: BB b 1.5bb / BU c" in out
        assert "T " not in out
        assert "R " not in out

    def test_full_streets(self, base_hand):
        base_hand.street_data = StreetData(
            board=BoardCards(flop=["Ah", "3s", "8c"], turn="7s", river="Jd"),
            actions=StreetActions(
                flop=[Action("Villain", "bet", amount=0.03), Action("Hero", "call", amount=0.03)],
                turn=[Action("Villain", "bet", amount=0.05), Action("Hero", "call", amount=0.05)],
                river=[Action("Villain", "bet", amount=0.1, all_in=True), Action("Hero", "call", amount=0.1, all_in=True)],
            ),
        )
        out = format_hand(base_hand, 5)
        assert "F Ah3s8c: BB b 1.5bb / BU c" in out
        assert "T 7s: BB b 2.5bb / BU c" in out
        assert "R Jd: BB a 5.0bb / BU c" in out  # Call remains 'c' even if all_in=True


class TestShowdownFormatting:
    def test_showdown_present(self, base_hand):
        base_hand.showdown = ShowdownData(
            villains=[ShowdownVillain("Villain", ["Th", "9h"], "straight")],
            result="lost",
        )
        out = format_hand(base_hand, 6)
        assert "SD: BB Th9h = straight" in out
        assert "Result: lost" in out

    def test_no_showdown_win(self, base_hand):
        base_hand.showdown = ShowdownData(villains=[], result="won")
        out = format_hand(base_hand, 7)
        assert "SD:" not in out
        assert "Result: won" in out

    def test_multiple_villains_showdown(self, base_hand):
        base_hand.position_map["Villain2"] = "SB"
        base_hand.showdown = ShowdownData(
            villains=[
                ShowdownVillain("Villain", ["Ks", "Qs"], "flush"),
                ShowdownVillain("Villain2", ["7d", "7c"], "pair"),
            ],
            result="won",
        )
        out = format_hand(base_hand, 8)
        assert "SD: BB KsQs = flush" in out
        assert "SD: SB 7d7c = pair" in out


class TestEdgeCases:
    def test_missing_position_map_entry(self, base_hand):
        base_hand.preflop_actions = [Action("UnknownPlayer", "fold")]
        out = format_hand(base_hand, 9)
        assert "PF: UNKNOWN f" in out

    def test_unknown_result(self, base_hand):
        base_hand.showdown = None
        out = format_hand(base_hand, 10)
        assert "Result: unknown" in out
