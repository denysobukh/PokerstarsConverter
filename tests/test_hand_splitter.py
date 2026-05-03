import pytest
from parser.hand_splitter import split_hands

# Minimal hand block: header line + a few action lines + ИТОГ
HAND_TEMPLATE = """Раздача PokerStars №{hand_id}:  Холдем Безлимитный ($0.01/$0.02 USD) - 03.05.2026 18:47:49 EET [03.05.2026 11:47:49 ВВ]
Стол 'Test' 6-max Баттон на месте №1
Место 1: Hero ($1.00 фишек)
Место 2: Villain ($1.00 фишек)
Villain: ставит малый блайнд $0.01
Hero: ставит большой блайнд $0.02
*** ЗАКРЫТЫЕ КАРТЫ ***
Карты Hero [Ah Kh]
Hero: делает колл $0.01
*** ИТОГ ***
"""

SEPARATOR = "*********** №{num} **************"


def _build_text(hand_ids: list[int]) -> str:
    """Build a synthetic file with *hand_ids* hands."""
    parts = ["Выписка Ваши последние N раздач"]
    for i, hid in enumerate(hand_ids, 1):
        parts.append(SEPARATOR.format(num=i))
        parts.append(HAND_TEMPLATE.format(hand_id=hid))
    return "\n\n".join(parts)


class TestSplitHandsEmpty:
    def test_empty_string(self):
        assert split_hands("") == []

    def test_whitespace_only(self):
        assert split_hands("   \n\n   ") == []

    def test_header_only(self):
        assert split_hands("Выписка Ваши последние 20 раздач") == []

    def test_garbage_no_hands(self):
        assert split_hands("some random text\nwithout hand markers") == []


class TestSplitHandsSingle:
    def test_one_hand(self):
        text = _build_text([100])
        hands = split_hands(text)
        assert len(hands) == 1
        assert "Раздача PokerStars №100" in hands[0]

    def test_one_hand_no_header(self):
        text = SEPARATOR.format(num=1) + "\n" + HAND_TEMPLATE.format(hand_id=42)
        hands = split_hands(text)
        assert len(hands) == 1


class TestSplitHandsMultiple:
    def test_two_hands(self):
        text = _build_text([10, 20])
        hands = split_hands(text)
        assert len(hands) == 2
        assert "№10" in hands[0]
        assert "№20" in hands[1]

    def test_five_hands(self):
        text = _build_text(list(range(1, 6)))
        assert len(split_hands(text)) == 5

    def test_hands_are_stripped(self):
        text = _build_text([1])
        hands = split_hands(text)
        assert hands[0] == hands[0].strip()
        assert not hands[0].startswith("\n")
        assert not hands[0].endswith("\n")


class TestSplitHandsSeparatorVariants:
    def test_fewer_asterisks(self):
        text = "******* №1 *******\n" + HAND_TEMPLATE.format(hand_id=1)
        assert len(split_hands(text)) == 1

    def test_more_asterisks(self):
        text = "*************** №1 ***************\n" + HAND_TEMPLATE.format(hand_id=1)
        assert len(split_hands(text)) == 1

    def test_multidigit_hand_number(self):
        text = "*********** №12345 **************\n" + HAND_TEMPLATE.format(hand_id=999)
        assert len(split_hands(text)) == 1


class TestSplitHandsEdgeCases:
    def test_consecutive_separators_no_content(self):
        text = "*********** №1 **************\n*********** №2 **************"
        assert split_hands(text) == []

    def test_trailing_text_after_last_hand(self):
        text = _build_text([1]) + "\n\nВ этом письме содержится важная информация"
        hands = split_hands(text)
        assert len(hands) == 1

    def test_blocks_without_раздача_prefix_rejected(self):
        text = "*********** №1 **************\nSome other text\n*********** №2 **************\n" + HAND_TEMPLATE.format(hand_id=2)
        hands = split_hands(text)
        assert len(hands) == 1
        assert "№2" in hands[0]
