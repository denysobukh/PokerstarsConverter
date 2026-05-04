import pytest
from parser.street_parser import (
    BoardCards,
    StreetActions,
    StreetData,
    parse_streets,
)

# ── Block builder ──────────────────────────────────────────────────────


def _build_block(
    flop_cards: list[str] | None = None,
    flop_actions: list[str] | None = None,
    turn_card: str | None = None,
    turn_actions: list[str] | None = None,
    river_card: str | None = None,
    river_actions: list[str] | None = None,
) -> str:
    """Build a minimal hand block with specified post-flop streets."""
    lines = [
        "Раздача PokerStars №1:  Холдем Безлимитный ($0.01/$0.02 USD)",
        "Стол 'Test' 6-max Баттон на месте №1",
        "*** ЗАКРЫТЫЕ КАРТЫ ***",
        "Карты Hero [Ah Kh]",
        "Hero: делает фолд",
    ]

    if flop_cards is not None:
        cards_str = " ".join(flop_cards)
        lines.append(f"*** ФЛОП *** [{cards_str}]")
        if flop_actions:
            lines.extend(flop_actions)

    if turn_card is not None:
        board = " ".join(flop_cards or [])
        lines.append(f"*** ТЕРН *** [{board}] [{turn_card}]")
        if turn_actions:
            lines.extend(turn_actions)

    if river_card is not None:
        board = " ".join(flop_cards or []) + " " + turn_card if turn_card else ""
        lines.append(f"*** РИВЕР *** [{board}] [{river_card}]")
        if river_actions:
            lines.extend(river_actions)

    lines.append("*** ИТОГ ***")
    return "\n".join(lines)


# ── Board card extraction ─────────────────────────────────────────────


class TestFlopCards:
    def test_three_cards(self):
        data = parse_streets(_build_block(flop_cards=["Jh", "8s", "Qc"]))
        assert data.board.flop == ["Jh", "8s", "Qc"]

    def test_empty_when_no_flop(self):
        data = parse_streets(_build_block())
        assert data.board.flop == []

    def test_various_ranks(self):
        data = parse_streets(_build_block(flop_cards=["Ad", "2c", "Ts"]))
        assert data.board.flop == ["Ad", "2c", "Ts"]

    def test_all_same_suit(self):
        data = parse_streets(_build_block(flop_cards=["7d", "5d", "2d"]))
        assert data.board.flop == ["7d", "5d", "2d"]


class TestTurnCard:
    def test_single_card(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Ah", "3s", "8c"],
                turn_card="7s",
            )
        )
        assert data.board.turn == "7s"

    def test_empty_when_no_turn(self):
        data = parse_streets(_build_block(flop_cards=["Ah", "3s", "8c"]))
        assert data.board.turn == ""

    def test_various_cards(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Kd", "5h", "7h"],
                turn_card="3h",
            )
        )
        assert data.board.turn == "3h"


class TestRiverCard:
    def test_single_card(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Ah", "3s", "8c"],
                turn_card="7s",
                river_card="Jd",
            )
        )
        assert data.board.river == "Jd"

    def test_empty_when_no_river(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Ah", "3s", "8c"],
                turn_card="7s",
            )
        )
        assert data.board.river == ""


# ── Flop actions ──────────────────────────────────────────────────────


class TestFlopActions:
    def test_bet_and_folds(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Jh", "8s", "Qc"],
                flop_actions=[
                    "V1: делает бет $0.02",
                    "Hero: делает фолд",
                ],
            )
        )
        assert len(data.actions.flop) == 2
        assert data.actions.flop[0].action_type == "bet"
        assert data.actions.flop[0].amount == 0.02
        assert data.actions.flop[1].action_type == "fold"

    def test_check_check(self):
        data = parse_streets(
            _build_block(
                flop_cards=["8c", "Jh", "3c"],
                flop_actions=[
                    "Hero: делает чек",
                    "V1: делает чек",
                ],
            )
        )
        assert len(data.actions.flop) == 2
        assert all(a.action_type == "check" for a in data.actions.flop)

    def test_bet_call(self):
        data = parse_streets(
            _build_block(
                flop_cards=["7s", "5c", "2c"],
                flop_actions=[
                    "V1: делает чек",
                    "V2: делает бет $0.06",
                    "Hero: делает колл $0.06",
                ],
            )
        )
        assert len(data.actions.flop) == 3
        assert data.actions.flop[0].action_type == "check"
        assert data.actions.flop[1].action_type == "bet"
        assert data.actions.flop[2].action_type == "call"

    def test_raise_all_in_flop(self):
        data = parse_streets(
            _build_block(
                flop_cards=["6c", "9c", "7d"],
                flop_actions=[
                    "Hero: делает чек",
                    "V1: делает чек",
                    "V2: делает бет $0.17",
                    "Hero: делает фолд",
                    "V1: делает рейз $3.12 $3.29 и олл-ин",
                ],
            )
        )
        assert len(data.actions.flop) == 5
        assert data.actions.flop[4].action_type == "raise"
        assert data.actions.flop[4].amount == 3.29
        assert data.actions.flop[4].all_in is True

    def test_empty_when_no_flop(self):
        data = parse_streets(_build_block())
        assert data.actions.flop == []


# ── Turn actions ──────────────────────────────────────────────────────


class TestTurnActions:
    def test_bet_and_fold(self):
        data = parse_streets(
            _build_block(
                flop_cards=["8c", "Jh", "3c"],
                flop_actions=["Hero: делает чек", "V1: делает чек"],
                turn_card="As",
                turn_actions=[
                    "Hero: делает бет $0.04",
                    "V1: делает фолд",
                ],
            )
        )
        assert len(data.actions.turn) == 2
        assert data.actions.turn[0].action_type == "bet"
        assert data.actions.turn[0].amount == 0.04
        assert data.actions.turn[1].action_type == "fold"

    def test_bet_call(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Ah", "3s", "8c"],
                flop_actions=["V1: делает бет $0.11", "Hero: делает колл $0.11"],
                turn_card="7s",
                turn_actions=[
                    "V1: делает бет $0.17",
                    "Hero: делает колл $0.17",
                ],
            )
        )
        assert len(data.actions.turn) == 2
        assert data.actions.turn[0].action_type == "bet"
        assert data.actions.turn[1].action_type == "call"

    def test_empty_when_no_turn(self):
        data = parse_streets(
            _build_block(flop_cards=["Ah", "3s", "8c"])
        )
        assert data.actions.turn == []


# ── River actions ─────────────────────────────────────────────────────


class TestRiverActions:
    def test_bet_all_in_call_all_in(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Ah", "3s", "8c"],
                flop_actions=["V1: делает бет $0.11", "Hero: делает колл $0.11"],
                turn_card="7s",
                turn_actions=["V1: делает бет $0.17", "Hero: делает колл $0.17"],
                river_card="Jd",
                river_actions=[
                    "V1: делает бет $1.57 и олл-ин",
                    "Hero: делает колл $1.16 и олл-ин",
                ],
            )
        )
        assert len(data.actions.river) == 2
        assert data.actions.river[0].action_type == "bet"
        assert data.actions.river[0].all_in is True
        assert data.actions.river[0].amount == 1.57
        assert data.actions.river[1].action_type == "call"
        assert data.actions.river[1].all_in is True
        assert data.actions.river[1].amount == 1.16

    def test_check_check(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Kd", "5h", "7h"],
                flop_actions=["Hero: делает чек", "V1: делает чек"],
                turn_card="3h",
                turn_actions=["Hero: делает чек", "V1: делает чек"],
                river_card="Ac",
                river_actions=[
                    "Hero: делает чек",
                    "V1: делает чек",
                ],
            )
        )
        assert len(data.actions.river) == 2
        assert all(a.action_type == "check" for a in data.actions.river)

    def test_empty_when_no_river(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Ah", "3s", "8c"],
                turn_card="7s",
            )
        )
        assert data.actions.river == []


# ── Street separation ─────────────────────────────────────────────────


class TestStreetSeparation:
    def test_actions_not_leak_between_streets(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Ah", "3s", "8c"],
                flop_actions=["V1: делает бет $0.11", "Hero: делает колл $0.11"],
                turn_card="7s",
                turn_actions=["V1: делает бет $0.17", "Hero: делает колл $0.17"],
                river_card="Jd",
                river_actions=[
                    "V1: делает бет $1.57 и олл-ин",
                    "Hero: делает колл $1.16 и олл-ин",
                ],
            )
        )
        assert len(data.actions.flop) == 2
        assert len(data.actions.turn) == 2
        assert len(data.actions.river) == 2

    def test_flop_ends_at_summary(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Jh", "8s", "Qc"],
                flop_actions=[
                    "V1: делает бет $0.02",
                    "Hero: делает фолд",
                ],
            )
        )
        assert len(data.actions.flop) == 2
        assert data.actions.turn == []
        assert data.actions.river == []

    def test_turn_ends_at_summary(self):
        data = parse_streets(
            _build_block(
                flop_cards=["8c", "Jh", "3c"],
                flop_actions=["Hero: делает чек", "V1: делает чек"],
                turn_card="As",
                turn_actions=[
                    "Hero: делает бет $0.04",
                    "V1: делает фолд",
                ],
            )
        )
        assert len(data.actions.turn) == 2
        assert data.actions.river == []


# ── Non-action lines skipped ──────────────────────────────────────────


class TestSkipNonActionStreets:
    def test_skips_pot_return_flop(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Jh", "8s", "Qc"],
                flop_actions=[
                    "V1: делает бет $0.02",
                    "Hero: делает фолд",
                    "Неуравненная ставка ($0.02) возвращается игроку V1",
                    "V1 получил $0.06 ( банк)",
                ],
            )
        )
        assert len(data.actions.flop) == 2

    def test_skips_leave_table_turn(self):
        data = parse_streets(
            _build_block(
                flop_cards=["7s", "5c", "2c"],
                flop_actions=[
                    "Hero: делает чек",
                    "Hero покидает стол",
                    "V2: делает бет $0.06",
                    "V1: делает колл $0.06",
                ],
                turn_card="7h",
                turn_actions=[
                    "V1: делает чек",
                    "V2: делает бет $0.17",
                    "V1: делает фолд",
                ],
            )
        )
        assert len(data.actions.flop) == 3
        assert len(data.actions.turn) == 3

    def test_skips_show_hand_river(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Ah", "3s", "8c"],
                flop_actions=["V1: делает бет $0.11", "Hero: делает колл $0.11"],
                turn_card="7s",
                turn_actions=["V1: делает бет $0.17", "Hero: делает колл $0.17"],
                river_card="Jd",
                river_actions=[
                    "V1: делает бет $1.57 и олл-ин",
                    "Hero: делает колл $1.16 и олл-ин",
                    "Неуравненная ставка ($0.41) возвращается игроку V1",
                ],
            )
        )
        assert len(data.actions.river) == 2


# ── Data types ─────────────────────────────────────────────────────────


class TestDataTypes:
    def test_returns_street_data(self):
        data = parse_streets(_build_block(flop_cards=["Ah", "3s", "8c"]))
        assert type(data).__name__ == "StreetData"

    def test_board_is_board_cards(self):
        data = parse_streets(_build_block(flop_cards=["Ah", "3s", "8c"]))
        assert type(data.board).__name__ == "BoardCards"

    def test_actions_is_street_actions(self):
        data = parse_streets(_build_block(flop_cards=["Ah", "3s", "8c"]))
        assert type(data.actions).__name__ == "StreetActions"

    def test_empty_block_returns_empty_data(self):
        data = parse_streets("")
        assert data.board.flop == []
        assert data.board.turn == ""
        assert data.board.river == ""
        assert data.actions.flop == []
        assert data.actions.turn == []
        assert data.actions.river == []


# ── Edge cases ────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_no_preflop_section(self):
        """Block with no preflop marker still parses streets."""
        block = (
            "*** ФЛОП *** [Ah 3s 8c]\n"
            "Hero: делает чек\n"
            "*** ИТОГ ***\n"
        )
        data = parse_streets(block)
        assert data.board.flop == ["Ah", "3s", "8c"]
        assert len(data.actions.flop) == 1

    def test_flop_then_showdown_no_turn_river(self):
        """Hand ends on flop, goes to showdown."""
        block = (
            "*** ФЛОП *** [Ah 3s 8c]\n"
            "Hero: делает чек\n"
            "V1: делает чек\n"
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "V1: открывает [Th 9h] (стрит [семерка - валет])\n"
        )
        data = parse_streets(block)
        assert data.board.flop == ["Ah", "3s", "8c"]
        assert len(data.actions.flop) == 2
        assert data.board.turn == ""
        assert data.board.river == ""

    def test_flop_then_turn_then_showdown_no_river(self):
        """Hand ends on turn, goes to showdown."""
        block = (
            "*** ФЛОП *** [Ah 3s 8c]\n"
            "Hero: делает чек\n"
            "*** ТЕРН *** [Ah 3s 8c] [7s]\n"
            "Hero: делает чек\n"
            "V1: делает чек\n"
            "*** ВСКРЫТИЕ КАРТ ***\n"
        )
        data = parse_streets(block)
        assert data.board.turn == "7s"
        assert len(data.actions.turn) == 2
        assert data.board.river == ""
        assert data.actions.river == []

    def test_player_name_with_digits_flop(self):
        data = parse_streets(
            _build_block(
                flop_cards=["Ah", "3s", "8c"],
                flop_actions=["Player123: делает бет $0.05"],
            )
        )
        assert data.actions.flop[0].player == "Player123"
