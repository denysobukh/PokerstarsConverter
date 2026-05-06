import pytest
from pokerstars_converter.parser.showdown_parser import (
    ShowdownData,
    ShowdownVillain,
    _translate_hand_name,
    parse_showdown,
)

# ── Block builders ─────────────────────────────────────────────────────


def _build_showdown_block(
    hero_name: str = "Hero",
    villain_name: str = "Villain",
    villain_cards: str = "Th 9h",
    villain_hand: str = "стрит [семерка - валет]",
    hero_cards: str = "Ad Td",
    hero_hand: str = "пару [тузы]",
    hero_result: str = "и проиграл , собрав",
) -> str:
    """Build a minimal hand block with a showdown section."""
    return (
        f"*** ВСКРЫТИЕ КАРТ ***\n"
        f"{villain_name}: открывает [{villain_cards}] ({villain_hand})\n"
        f"{hero_name}: открывает [{hero_cards}] ({hero_hand})\n"
        f"{villain_name} получил $3.06 ( банк)\n"
        f"*** ИТОГ ***\n"
        f"Место 1: {hero_name} {hero_result} {hero_hand}\n"
        f"Место 2: {villain_name} открыл [{villain_cards}] и выиграл ($3.06) , собрав {villain_hand}\n"
    )


def _build_no_showdown_block(
    hero_name: str = "Hero",
    result_line: str = "сделал фолд до Флоп (не ставил)",
) -> str:
    """Build a minimal hand block without a showdown section."""
    return (
        f"*** ИТОГ ***\n"
        f"Место 1: {hero_name} {result_line}\n"
    )


# ── Hand name translation ──────────────────────────────────────────────


class TestTranslateHandName:
    def test_straight(self):
        assert _translate_hand_name("стрит [семерка - валет]") == "straight"

    def test_pair(self):
        assert _translate_hand_name("пару [тузы]") == "pair"

    def test_pair_variants(self):
        assert _translate_hand_name("пару [четверки]") == "pair"
        assert _translate_hand_name("пару [дамы]") == "pair"
        assert _translate_hand_name("пару [тройки]") == "pair"

    def test_high_card(self):
        assert _translate_hand_name("старшую карту [туз]") == "high card"
        assert _translate_hand_name("старшую карту [король]") == "high card"

    def test_two_pair(self):
        assert _translate_hand_name("две пары [тузы и короли]") == "two pair"

    def test_set_trips(self):
        assert _translate_hand_name("тройку [тузы]") == "set"

    def test_flush(self):
        assert _translate_hand_name("флеш [черви]") == "flush"

    def test_full_house(self):
        assert _translate_hand_name("фулл-хаус [тузы на королях]") == "full house"

    def test_quads(self):
        assert _translate_hand_name("каретку [тузы]") == "quads"

    def test_straight_flush(self):
        assert _translate_hand_name("стрит-флеш [черви]") == "straight flush"

    def test_royal_flush(self):
        assert _translate_hand_name("роял-флеш [черви]") == "royal flush"

    def test_unknown_hand(self):
        assert _translate_hand_name("какая-то дичь") == "unknown"


# ── Showdown villain parsing ───────────────────────────────────────────


class TestParseShowdownVillains:
    def test_single_villain_parsed(self):
        block = _build_showdown_block()
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert len(data.villains) == 1
        v = data.villains[0]
        assert v.player == "Villain"
        assert v.cards == ["Th", "9h"]
        assert v.hand_name == "straight"

    def test_villain_hand_high_card(self):
        block = _build_showdown_block(
            villain_cards="Jc Ts",
            villain_hand="старшую карту [туз] - король+валет+десятка (кикер)",
            hero_result="и проиграл , собрав",
            hero_hand="старшую карту [туз]",
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert len(data.villains) == 1
        assert data.villains[0].hand_name == "high card"

    def test_villain_mucks_hand(self):
        """When villain mucks, they are not included in villains list."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "Hero: открывает [3c Ah] (пару [тройки])\n"
            "Villain: сбрасывает руку\n"
            "Hero получил $0.04 ( банк)\n"
            "*** ИТОГ ***\n"
            "Место 1: Hero открыл [3c Ah] и выиграл ($0.04) , собрав пару [тройки]\n"
            "Место 2: Villain сбросил [2h Jc]\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert len(data.villains) == 0
        assert data.result == "won"

    def test_multiple_villains(self):
        """Two villains show down against hero."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "V1: открывает [Th 9h] (стрит [семерка - валет])\n"
            "V2: открывает [Ks Qs] (пару [дамы])\n"
            "Hero: открывает [Ad Td] (пару [тузы])\n"
            "V1 получил $5.00 ( банк)\n"
            "*** ИТОГ ***\n"
            "Место 1: Hero открыл [Ad Td] и проиграл , собрав пару [тузы]\n"
            "Место 2: V1 открыл [Th 9h] и выиграл ($5.00) , собрав стрит [семерка - валет]\n"
            "Место 3: V2 открыл [Ks Qs] и проиграл , собрав пару [дамы]\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert len(data.villains) == 2
        assert data.villains[0].player == "V1"
        assert data.villains[0].hand_name == "straight"
        assert data.villains[1].player == "V2"
        assert data.villains[1].hand_name == "pair"

    def test_hero_cards_not_in_villains(self):
        """Hero's own shown cards are excluded from the villains list."""
        block = _build_showdown_block()
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert all(v.player != "Hero" for v in data.villains)


# ── Result parsing ─────────────────────────────────────────────────────


class TestResultParsing:
    def test_hero_wins_showdown(self):
        block = _build_showdown_block(
            hero_result="открыл [8d Ac] и выиграл ($0.05) , собрав",
            hero_hand="пару [дамы]",
        )
        # Need to fix the summary line format for wins
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "Villain: открывает [Th 9h] (пару [дамы])\n"
            "Hero: открывает [8d Ac] (пару [дамы] - туз (кикер))\n"
            "Hero получил $0.05 ( банк)\n"
            "*** ИТОГ ***\n"
            "Место 1: Hero открыл [8d Ac] и выиграл ($0.05) , собрав пару [дамы]\n"
            "Место 2: Villain открыл [Th 9h] и проиграл , собрав пару [дамы]\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "won"

    def test_hero_loses_showdown(self):
        block = _build_showdown_block()
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "lost"

    def test_hero_folds_preflop(self):
        block = _build_no_showdown_block(
            result_line="сделал фолд до Флоп (не ставил)"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "fold"

    def test_hero_folds_preflop_with_blind(self):
        block = _build_no_showdown_block(
            result_line="(малый блайнд) сделал фолд до Флоп"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "fold"

    def test_hero_folds_flop(self):
        block = _build_no_showdown_block(
            result_line="(баттон) сделал фолд на Флоп"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "fold"

    def test_hero_wins_no_showdown(self):
        """Hero wins when all villains fold (no showdown marker)."""
        block = _build_no_showdown_block(
            result_line="(малый блайнд) собрал ($0.04)"
        )
        data = parse_showdown(block, "Hero")
        assert data is None  # No showdown, hero didn't fold

    def test_hero_result_unknown(self):
        """When hero's summary line is not found."""
        block = (
            "*** ИТОГ ***\n"
            "Место 2: Villain собрал ($0.02)\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is None  # No showdown, hero didn't fold, result unknown


# ── No showdown cases ─────────────────────────────────────────────────


class TestNoShowdown:
    def test_all_fold_preflop_hero_not_fold(self):
        """No showdown marker, hero didn't fold → None."""
        block = (
            "*** ИТОГ ***\n"
            "Место 1: Villain собрал ($0.05)\n"
            "Место 2: Hero сделал фолд до Флоп\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None  # Hero folded
        assert data.result == "fold"

    def test_no_showdown_hero_wins(self):
        """No showdown marker, hero collected pot → None."""
        block = (
            "*** ИТОГ ***\n"
            "Место 1: Hero собрал ($0.04)\n"
            "Место 2: Villain сделал фолд на Терн\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is None

    def test_empty_block(self):
        data = parse_showdown("", "Hero")
        assert data is None


# ── Full showdown hands ────────────────────────────────────────────────


class TestFullShowdownHands:
    def test_hand_11_style_loses(self):
        """Based on hand #11 from sample: hero loses to straight."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "jonnyjm: открывает [Th 9h] (стрит [семерка - валет])\n"
            "Avviee: открывает [Ad Td] (пару [тузы])\n"
            "jonnyjm получил $3.06 ( банк)\n"
            "*** ИТОГ ***\n"
            "Место 1: Avviee открыл [Ad Td] и проиграл , собрав пару [тузы]\n"
            "Место 3: jonnyjm (малый блайнд) открыл [Th 9h] и выиграл ($3.06) , собрав стрит [семерка - валет]\n"
        )
        data = parse_showdown(block, "Avviee")
        assert data is not None
        assert data.result == "lost"
        assert len(data.villains) == 1
        assert data.villains[0].player == "jonnyjm"
        assert data.villains[0].cards == ["Th", "9h"]
        assert data.villains[0].hand_name == "straight"

    def test_hand_16_style_loses_high_card(self):
        """Based on hand #16: hero loses high card kickers."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "Avviee: открывает [Jd 9d] (старшую карту [туз])\n"
            "Fede3M: открывает [Jc Ts] (старшую карту [туз] - король+валет+десятка (кикер))\n"
            "Fede3M получил $0.12 ( банк)\n"
            "*** ИТОГ ***\n"
            "Место 3: Avviee открыл [Jd 9d] и проиграл , собрав старшую карту [туз]\n"
            "Место 4: Fede3M (баттон) открыл [Jc Ts] и выиграл ($0.12) , собрав старшую карту [туз]\n"
        )
        data = parse_showdown(block, "Avviee")
        assert data is not None
        assert data.result == "lost"
        assert len(data.villains) == 1
        assert data.villains[0].player == "Fede3M"
        assert data.villains[0].hand_name == "high card"

    def test_hand_19_style_loses_pair(self):
        """Based on hand #19: hero loses, villain has pair."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "Avviee: открывает [Tc 5c] (старшую карту [король])\n"
            "SamitokD: открывает [4d 4s] (пару [четверки])\n"
            "SamitokD получил $0.05 ( банк)\n"
            "*** ИТОГ ***\n"
            "Место 1: SamitokD (баттон) открыл [4d 4s] и выиграл ($0.05) , собрав пару [четверки]\n"
            "Место 3: Avviee (большой блайнд) открыл [Tc 5c] и проиграл , собрав старшую карту [король]\n"
        )
        data = parse_showdown(block, "Avviee")
        assert data is not None
        assert data.result == "lost"
        assert len(data.villains) == 1
        assert data.villains[0].hand_name == "pair"

    def test_hand_21_style_wins(self):
        """Based on hand #21: hero wins at showdown."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "booster61: открывает [5s Kh] (пару [дамы])\n"
            "Avviee: открывает [8d Ac] (пару [дамы] - туз (кикер))\n"
            "Avviee получил $0.05 ( банк)\n"
            "*** ИТОГ ***\n"
            "Место 3: Avviee (баттон) открыл [8d Ac] и выиграл ($0.05) , собрав пару [дамы]\n"
            "Место 6: booster61 (большой блайнд) открыл [5s Kh] и проиграл , собрав пару [дамы]\n"
        )
        data = parse_showdown(block, "Avviee")
        assert data is not None
        assert data.result == "won"
        assert len(data.villains) == 1
        assert data.villains[0].player == "booster61"
        assert data.villains[0].hand_name == "pair"

    def test_hand_124_style_wins_villain_mucks(self):
        """Based on hand #124: hero wins, villain mucks."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "Avviee: открывает [3c Ah] (пару [тройки])\n"
            "Lorpugo: сбрасывает руку\n"
            "Avviee получил $0.04 ( банк)\n"
            "*** ИТОГ ***\n"
            "Место 1: Avviee (малый блайнд) открыл [3c Ah] и выиграл ($0.04) , собрав пару [тройки]\n"
            "Место 2: Lorpugo (большой блайнд) сбросил [2h Jc]\n"
        )
        data = parse_showdown(block, "Avviee")
        assert data is not None
        assert data.result == "won"
        assert len(data.villains) == 0  # Villain mucked, no cards shown


# ── Hero fold cases ────────────────────────────────────────────────────


class TestHeroFold:
    def test_fold_preflop_no_blind(self):
        """Hero folds preflop, no chips invested."""
        block = (
            "*** ИТОГ ***\n"
            "Место 1: Hero сделал фолд до Флоп (не ставил)\n"
            "Место 2: Villain собрал ($0.04)\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "fold"
        assert data.villains == []

    def test_fold_preflop_as_bb(self):
        """Hero folds preflop from BB position."""
        block = (
            "*** ИТОГ ***\n"
            "Место 1: Hero (большой блайнд) сделал фолд до Флоп\n"
            "Место 2: Villain собрал ($0.05)\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "fold"

    def test_fold_flop(self):
        """Hero folds on flop."""
        block = (
            "*** ИТОГ ***\n"
            "Место 1: Hero (баттон) сделал фолд на Флоп\n"
            "Место 2: Villain собрал ($0.06)\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "fold"

    def test_fold_turn(self):
        """Hero folds on turn."""
        block = (
            "*** ИТОГ ***\n"
            "Место 1: Hero (большой блайнд) сделал фолд на Терн\n"
            "Место 2: Villain собрал ($0.10)\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "fold"


# ── Hero wins no showdown ─────────────────────────────────────────────


class TestHeroWinsNoShowdown:
    def test_villain_folds_flop(self):
        block = (
            "*** ИТОГ ***\n"
            "Место 1: Hero (баттон) собрал ($0.04)\n"
            "Место 2: Villain сделал фолд на Флоп\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is None

    def test_villain_folds_preflop(self):
        block = (
            "*** ИТОГ ***\n"
            "Место 1: Hero собрал ($0.02)\n"
            "Место 2: Villain сделал фолд до Флоп\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is None


# ── Edge cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_hero_name_with_digits(self):
        """Hero name contains digits."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "V1: открывает [Ks Qs] (пару [дамы])\n"
            "Hero123: открывает [As Ks] (пару [тузы])\n"
            "Hero123 получил $1.00 ( банк)\n"
            "*** ИТОГ ***\n"
            "Место 1: Hero123 открыл [As Ks] и выиграл ($1.00) , собрав пару [тузы]\n"
            "Место 2: V1 открыл [Ks Qs] и проиграл , собрав пару [дамы]\n"
        )
        data = parse_showdown(block, "Hero123")
        assert data is not None
        assert data.result == "won"

    def test_showdown_with_non_showdown_lines(self):
        """Non-card-showing lines in showdown section are skipped."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "V1: открывает [Ks Qs] (пару [дамы])\n"
            "Hero: открывает [As Ks] (пару [тузы])\n"
            "Hero получил $1.00 ( банк)\n"
            "SomeOtherPlayer покидает стол\n"
            "*** ИТОГ ***\n"
            "Место 1: Hero открыл [As Ks] и выиграл ($1.00) , собрав пару [тузы]\n"
            "Место 2: V1 открыл [Ks Qs] и проиграл , собрав пару [дамы]\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert data.result == "won"
        assert len(data.villains) == 1

    def test_showdown_section_before_summary(self):
        """Showdown section ends at summary marker."""
        block = (
            "*** ВСКРЫТИЕ КАРТ ***\n"
            "V1: открывает [Ks Qs] (пару [дамы])\n"
            "Hero: открывает [As Ks] (пару [тузы])\n"
            "*** ИТОГ ***\n"
            "Место 1: Hero открыл [As Ks] и выиграл ($1.00) , собрав пару [тузы]\n"
            "Место 2: V1 открыл [Ks Qs] и проиграл , собрав пару [дамы]\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is not None
        assert len(data.villains) == 1

    def test_no_showdown_no_summary(self):
        """Completely empty block."""
        data = parse_showdown("", "Hero")
        assert data is None

    def test_hero_not_in_summary(self):
        """Hero's result line is missing from summary."""
        block = (
            "*** ИТОГ ***\n"
            "Место 2: Villain собрал ($0.04)\n"
        )
        data = parse_showdown(block, "Hero")
        assert data is None  # No showdown, no fold, unknown

    def test_dataclass_defaults(self):
        """ShowdownData defaults are correct."""
        data = ShowdownData()
        assert data.villains == []
        assert data.result == "unknown"

    def test_villain_dataclass(self):
        """ShowdownVillain fields are correct."""
        v = ShowdownVillain(player="V1", cards=["As", "Ks"], hand_name="pair")
        assert v.player == "V1"
        assert v.cards == ["As", "Ks"]
        assert v.hand_name == "pair"
