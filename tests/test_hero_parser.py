from parser.hero_parser import (
    HeroInfo,
    card_rank,
    card_suit,
    extract_hero,
    format_hero_cards,
)

# ── Block builder ──────────────────────────────────────────────────────


def _build_block(hero_name: str, cards: str) -> str:
    """Build a minimal hand block with a hero cards line."""
    return (
        "Раздача PokerStars №1:  Холдем Безлимитный ($0.01/$0.02 USD)\n"
        "Стол 'Test' 6-max Баттон на месте №1\n"
        "Место 1: Hero ($1.00 фишек)\n"
        "*** ЗАКРЫТЫЕ КАРТЫ ***\n"
        f"Карты {hero_name} [{cards}]\n"
        "*** ИТОГ ***\n"
    )


# ── extract_hero ───────────────────────────────────────────────────────


class TestExtractHero:
    def test_basic(self):
        h = extract_hero(_build_block("Hero", "Ah Kh"))
        assert h is not None
        assert h.name == "Hero"
        assert h.card1 == "Ah"
        assert h.card2 == "Kh"

    def test_hero_name_from_sample(self):
        h = extract_hero(_build_block("Avviee", "9c Ts"))
        assert h.name == "Avviee"
        assert h.card1 == "9c"
        assert h.card2 == "Ts"

    def test_pocket_pair(self):
        h = extract_hero(_build_block("Hero", "7d 7h"))
        assert h.card1 == "7d"
        assert h.card2 == "7h"

    def test_suited_cards(self):
        h = extract_hero(_build_block("Hero", "Ad Td"))
        assert h.card1 == "Ad"
        assert h.card2 == "Td"

    def test_none_when_no_cards_line(self):
        block = (
            "Раздача PokerStars №1:  Холдем Безлимитный ($0.01/$0.02 USD)\n"
            "Стол 'Test' 6-max Баттон на месте №1\n"
            "*** ИТОГ ***\n"
        )
        assert extract_hero(block) is None

    def test_none_on_empty_block(self):
        assert extract_hero("") is None

    def test_hero_name_with_digits(self):
        h = extract_hero(_build_block("Player123", "Qs Jc"))
        assert h.name == "Player123"

    def test_cards_in_different_section_ignored(self):
        """Only the first Карты line (preflop) is used."""
        block = (
            "Раздача PokerStars №1:  Холдем Безлимитный ($0.01/$0.02 USD)\n"
            "*** ЗАКРЫТЫЕ КАРТЫ ***\n"
            "Карты Hero [Ah Kh]\n"
            "*** ФЛОП ***\n"
            "Карты Villain [Qd Jd]\n"
        )
        h = extract_hero(block)
        assert h.name == "Hero"
        assert h.card1 == "Ah"

    def test_returns_hero_info_type(self):
        h = extract_hero(_build_block("Hero", "Ah Kh"))
        assert type(h).__name__ == "HeroInfo"


# ── card_rank / card_suit ─────────────────────────────────────────────


class TestCardParts:
    def test_rank_ace(self):
        assert card_rank("Ad") == "A"

    def test_rank_ten(self):
        assert card_rank("Ts") == "T"

    def test_rank_number(self):
        assert card_rank("9c") == "9"

    def test_rank_face(self):
        assert card_rank("Kh") == "K"
        assert card_rank("Qd") == "Q"
        assert card_rank("Js") == "J"

    def test_suit_all_four(self):
        assert card_suit("Ad") == "d"
        assert card_suit("Ah") == "h"
        assert card_suit("As") == "s"
        assert card_suit("Ac") == "c"

    def test_empty_on_bad_input(self):
        assert card_rank("") == ""
        assert card_suit("") == ""


# ── format_hero_cards ─────────────────────────────────────────────────


class TestFormatHeroCards:
    # Pocket pairs
    def test_pair_7s(self):
        assert format_hero_cards("7d", "7h") == "7d7h"

    def test_pair_aces(self):
        assert format_hero_cards("As", "Ad") == "AsAd"

    def test_pair_kings(self):
        assert format_hero_cards("Kh", "Kc") == "KhKc"

    def test_pair_tens(self):
        assert format_hero_cards("Ts", "Td") == "TsTd"

    def test_pair_nines(self):
        assert format_hero_cards("9c", "9s") == "9c9s"

    # Suited (non-pair, same suit)
    def test_suited_AT(self):
        assert format_hero_cards("Ad", "Td") == "AdTd"

    def test_suited_KJ(self):
        assert format_hero_cards("Ks", "Js") == "KsJs"

    def test_suited_98(self):
        assert format_hero_cards("9h", "8h") == "9h8h"

    # Offsuit (non-pair, different suit)
    def test_offsuit_AK(self):
        assert format_hero_cards("Ah", "Kh") == "AhKh"

    def test_offsuit_QJ(self):
        assert format_hero_cards("Qs", "Jc") == "QsJc"

    def test_offsuit_72(self):
        assert format_hero_cards("7d", "2s") == "7d2s"

    # Edge: empty cards
    def test_empty_cards(self):
        assert format_hero_cards("", "") == ""
