import pytest
import sys
from unittest.mock import patch, mock_open

from converter import parse_hand, main
from parser.hand_splitter import split_hands

# Full hand with flop, turn, river, showdown
# Button at seat 2, Hero at seat 1 -> Hero is BB, Villain is BU
FULL_HAND = """Раздача PokerStars №2: ($0.01/$0.02 USD) NL Hold'em - 2023/01/01 12:00:00
Баттон на месте №2
Место 1: Hero ($2.00 фишек)
Место 2: Villain ($2.00 фишек)
Villain: ставит малый блайнд $0.01
Hero: ставит большой блайнд $0.02
*** ЗАКРЫТЫЕ КАРТЫ ***
Карты Hero [Ad Td]
Hero: делает рейз $0.02 $0.04
Villain: делает колл $0.04
*** ФЛОП *** [Ah 3s 8c]
Villain: делает бет $0.03
Hero: делает колл $0.03
*** ТЕРН *** [Ah 3s 8c] [7s]
Villain: делает бет $0.05
Hero: делает колл $0.05
*** РИВЕР *** [Ah 3s 8c 7s] [Jd]
Villain: делает бет $0.10 и олл-ин
Hero: делает колл $0.10 и олл-ин
*** ВСКРЫТИЕ КАРТ ***
Villain: открывает [Th 9h] (стрит [семерка - валет])
*** ИТОГ ***
Место 1: Hero (большой блайнд) открыл [Ad Td] и проиграл , собрав пару [тузы]
Место 2: Villain (малый блайнд) открыл [Th 9h] и выиграл ($0.34) , собрав стрит [семерка - валет]
"""

# Hero folds preflop
FOLD_HAND = """Раздача PokerStars №3: ($0.01/$0.02 USD) NL Hold'em - 2023/01/01 12:00:00
Баттон на месте №2
Место 1: Hero ($2.00 фишек)
Место 2: Villain ($2.00 фишек)
Villain: ставит малый блайнд $0.01
Hero: ставит большой блайнд $0.02
*** ЗАКРЫТЫЕ КАРТЫ ***
Карты Hero [7s 7c]
Hero: делает фолд
*** ИТОГ ***
Место 1: Hero (большой блайнд) сделал фолд до Флоп (не ставил)
"""

# Hero absent: no "Карты" line at all
HERO_ABSENT_HAND = """Раздача PokerStars №4: ($0.01/$0.02 USD) NL Hold'em - 2023/01/01 12:00:00
Баттон на месте №1
Место 1: PlayerA ($2.00 фишек)
Место 2: PlayerB ($2.00 фишек)
PlayerB: ставит малый блайнд $0.01
PlayerA: ставит большой блайнд $0.02
*** ЗАКРЫТЫЕ КАРТЫ ***
PlayerA: делает рейз $0.02 $0.04
PlayerB: делает фолд
*** ИТОГ ***
Место 1: PlayerA (большой блайнд) собрал ($0.03)
"""


def _build_text(hands: list[str]) -> str:
    """Wrap hand blocks with separators to simulate a real file."""
    parts = ["Выписка Ваши последние 20 раздач"]
    for i, hand in enumerate(hands, 1):
        parts.append(f"*********** №{i} **************")
        parts.append(hand)
    return "\n\n".join(parts)


class TestParseHand:
    def test_parses_full_hand(self):
        hand = parse_hand(FULL_HAND)
        assert hand is not None
        assert hand.hero_name == "Hero"
        assert hand.hero_cards == "AdTd"
        assert hand.hero_position == "BB"
        assert hand.eff_stack_bb == 100
        assert "BU" in hand.villain_positions  # Heads-up: Villain is BU
        assert hand.showdown is not None
        assert hand.showdown.result == "lost"

    def test_parses_fold_hand(self):
        hand = parse_hand(FOLD_HAND)
        assert hand is not None
        assert hand.hero_cards == "7s7c"
        assert hand.showdown is not None
        assert hand.showdown.result == "fold"

    def test_skips_hero_absent(self):
        hand = parse_hand(HERO_ABSENT_HAND)
        assert hand is None


class TestIntegrationPipeline:
    def test_sequential_numbering(self):
        text = _build_text([FULL_HAND, FOLD_HAND])
        raw = split_hands(text)
        outputs = []
        counter = 0
        for block in raw:
            hand = parse_hand(block)
            if hand:
                counter += 1
                outputs.append(hand.hero_cards)
        assert counter == 2
        assert outputs == ["AdTd", "7s7c"]

    def test_hero_absent_does_not_increment_counter(self):
        text = _build_text([FULL_HAND, HERO_ABSENT_HAND, FOLD_HAND])
        raw = split_hands(text)
        counter = 0
        for block in raw:
            hand = parse_hand(block)
            if hand:
                counter += 1
        assert counter == 2  # Hero absent hand skipped

    def test_cli_output_structure(self, capsys):
        text = _build_text([FULL_HAND])
        with patch("sys.argv", ["converter.py", "dummy.txt"]):
            with patch("builtins.open", mock_open(read_data=text)):
                main()

        captured = capsys.readouterr()
        assert "Hand#1" in captured.out
        assert "AdTd BB 100bb vs BU" in captured.out
        assert "Result: lost" in captured.out

    def test_cli_file_not_found(self, capsys):
        with patch("sys.argv", ["converter.py", "nonexistent.txt"]):
            with patch("builtins.open", side_effect=FileNotFoundError):
                with pytest.raises(SystemExit) as exc_info:
                    main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()
