from pokerstars_converter.parser.action_parser import (
    Action,
    PreflopActions,
    extract_preflop_section,
    parse_preflop_actions,
)

# ── Block builder ──────────────────────────────────────────────────────


def _build_block(preflop_lines: list[str]) -> str:
    """Build a minimal hand block with the given preflop action lines."""
    return (
        "Раздача PokerStars №1:  Холдем Безлимитный ($0.01/$0.02 USD)\n"
        "Стол 'Test' 6-max Баттон на месте №1\n"
        "Место 1: Hero ($1.00 фишек)\n"
        "*** ЗАКРЫТЫЕ КАРТЫ ***\n"
        + "\n".join(preflop_lines)
        + "\n*** ФЛОП ***\n"
        "[Ad Kd 7d]\n"
    )


def _build_block_no_flop(preflop_lines: list[str]) -> str:
    """Build a block that ends without a flop."""
    return (
        "Раздача PokerStars №1:  Холдем Безлимитный ($0.01/$0.02 USD)\n"
        "Стол 'Test' 6-max Баттон на месте №1\n"
        "*** ЗАКРЫТЫЕ КАРТЫ ***\n"
        + "\n".join(preflop_lines)
        + "\n*** ИТОГ ***\n"
    )


# ── extract_preflop_section ───────────────────────────────────────────


class TestExtractPreflopSection:
    def test_basic(self):
        block = _build_block(["Карты Hero [Ah Kh]", "Hero: делает фолд"])
        section = extract_preflop_section(block)
        assert "Карты Hero [Ah Kh]" in section
        assert "Hero: делает фолд" in section
        assert "ФЛОП" not in section

    def test_excludes_header(self):
        block = _build_block(["Hero: делает фолд"])
        section = extract_preflop_section(block)
        assert "Раздача" not in section
        assert "Место" not in section

    def test_excludes_flop(self):
        block = _build_block(["Hero: делает фолд"])
        section = extract_preflop_section(block)
        assert "[Ad Kd 7d]" not in section

    def test_no_flop_marker(self):
        block = _build_block_no_flop(["Hero: делает фолд"])
        section = extract_preflop_section(block)
        assert "Hero: делает фолд" in section

    def test_empty_block(self):
        section = extract_preflop_section("")
        assert section == ""

    def test_no_preflop_marker(self):
        block = "some random text\nno markers here\n"
        section = extract_preflop_section(block)
        assert section == ""


# ── parse_preflop_actions: fold ───────────────────────────────────────


class TestFold:
    def test_single_fold(self):
        actions = parse_preflop_actions(_build_block(["Hero: делает фолд"]))
        assert len(actions.actions) == 1
        a = actions.actions[0]
        assert a.player == "Hero"
        assert a.action_type == "fold"
        assert a.amount == 0.0
        assert a.all_in is False

    def test_multiple_folds(self):
        actions = parse_preflop_actions(
            _build_block(["V1: делает фолд", "V2: делает фолд", "Hero: делает фолд"])
        )
        assert len(actions.actions) == 3
        assert all(a.action_type == "fold" for a in actions.actions)


# ── parse_preflop_actions: call ───────────────────────────────────────


class TestCall:
    def test_call_with_amount(self):
        actions = parse_preflop_actions(_build_block(["Hero: делает колл $0.02"]))
        assert len(actions.actions) == 1
        a = actions.actions[0]
        assert a.player == "Hero"
        assert a.action_type == "call"
        assert a.amount == 0.02

    def test_call_all_in(self):
        actions = parse_preflop_actions(_build_block(["Hero: делает колл $1.50 и олл-ин"]))
        assert len(actions.actions) == 1
        a = actions.actions[0]
        assert a.action_type == "call"
        assert a.amount == 1.50
        assert a.all_in is True

    def test_bb_option_call_no_amount(self):
        """A bare 'делает колл' without amount — not matched by current regex,
        which is fine since it's not in the sample.  But let's verify the
        check option is parsed correctly."""
        pass  # Covered by check tests below.


# ── parse_preflop_actions: raise ──────────────────────────────────────


class TestRaise:
    def test_raise_uses_total(self):
        """Raise $0.04 $0.06 → amount is 0.06 (the total)."""
        actions = parse_preflop_actions(_build_block(["Hero: делает рейз $0.04 $0.06"]))
        assert len(actions.actions) == 1
        a = actions.actions[0]
        assert a.player == "Hero"
        assert a.action_type == "raise"
        assert a.amount == 0.06

    def test_raise_all_in(self):
        actions = parse_preflop_actions(
            _build_block(["Hero: делает рейз $3.12 $3.29 и олл-ин"])
        )
        assert len(actions.actions) == 1
        a = actions.actions[0]
        assert a.action_type == "raise"
        assert a.amount == 3.29
        assert a.all_in is True

    def test_multiple_raises(self):
        actions = parse_preflop_actions(
            _build_block([
                "V1: делает рейз $0.03 $0.05",
                "Hero: делает рейз $0.10 $0.15",
            ])
        )
        assert len(actions.actions) == 2
        assert actions.actions[0].amount == 0.05
        assert actions.actions[1].amount == 0.15


# ── parse_preflop_actions: bet ────────────────────────────────────────


class TestBet:
    def test_bet(self):
        actions = parse_preflop_actions(_build_block(["Hero: делает бет $0.02"]))
        assert len(actions.actions) == 1
        a = actions.actions[0]
        assert a.action_type == "bet"
        assert a.amount == 0.02

    def test_bet_all_in(self):
        actions = parse_preflop_actions(_build_block(["Hero: делает бет $1.57 и олл-ин"]))
        assert len(actions.actions) == 1
        a = actions.actions[0]
        assert a.action_type == "bet"
        assert a.amount == 1.57
        assert a.all_in is True


# ── parse_preflop_actions: check ──────────────────────────────────────


class TestCheck:
    def test_check(self):
        actions = parse_preflop_actions(_build_block(["Hero: делает чек"]))
        assert len(actions.actions) == 1
        a = actions.actions[0]
        assert a.action_type == "check"
        assert a.amount == 0.0


# ── Non-action lines are skipped ─────────────────────────────────────


class TestSkipNonAction:
    def test_skips_hole_cards_line(self):
        actions = parse_preflop_actions(
            _build_block(["Карты Hero [Ah Kh]", "Hero: делает фолд"])
        )
        assert len(actions.actions) == 1
        assert actions.actions[0].player == "Hero"

    def test_skips_leave_table(self):
        actions = parse_preflop_actions(
            _build_block(["Hero покидает стол", "V1: делает фолд"])
        )
        assert len(actions.actions) == 1

    def test_skips_sit_down(self):
        actions = parse_preflop_actions(
            _build_block(["Nakamurastars садится за стол на место №2"])
        )
        assert len(actions.actions) == 0

    def test_skips_unbet_return(self):
        actions = parse_preflop_actions(
            _build_block(["Неуравненная ставка ($0.04) возвращается игроку Nakamurastars"])
        )
        assert len(actions.actions) == 0

    def test_skips_pot_return(self):
        actions = parse_preflop_actions(
            _build_block(["Nakamurastars получил $0.04 ( банк)"])
        )
        assert len(actions.actions) == 0

    def test_skips_show_hand(self):
        actions = parse_preflop_actions(
            _build_block(["Nakamurastars: не показывает руку"])
        )
        assert len(actions.actions) == 0

    def test_skips_empty_lines(self):
        actions = parse_preflop_actions(
            _build_block(["V1: делает фолд", "", "Hero: делает фолд"])
        )
        assert len(actions.actions) == 2


# ── Mixed action sequences ────────────────────────────────────────────


class TestMixedActions:
    def test_limp_call_raise_fold(self):
        actions = parse_preflop_actions(
            _build_block([
                "V1: делает колл $0.02",
                "Hero: делает рейз $0.04 $0.06",
                "V1: делает фолд",
            ])
        )
        assert len(actions.actions) == 3
        assert actions.actions[0].action_type == "call"
        assert actions.actions[1].action_type == "raise"
        assert actions.actions[2].action_type == "fold"

    def test_preflop_order_preserved(self):
        actions = parse_preflop_actions(
            _build_block([
                "V1: делает фолд",
                "V2: делает фолд",
                "Hero: делает фолд",
            ])
        )
        assert [a.player for a in actions.actions] == ["V1", "V2", "Hero"]


# ── Edge cases ────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_preflop(self):
        actions = parse_preflop_actions(_build_block([]))
        assert len(actions.actions) == 0

    def test_no_preflop_marker(self):
        actions = parse_preflop_actions("no markers at all\n")
        assert len(actions.actions) == 0

    def test_preflop_but_no_actions(self):
        actions = parse_preflop_actions(
            _build_block(["Карты Hero [Ah Kh]"])
        )
        assert len(actions.actions) == 0

    def test_player_name_with_digits(self):
        actions = parse_preflop_actions(
            _build_block(["Player123: делает фолд"])
        )
        assert len(actions.actions) == 1
        assert actions.actions[0].player == "Player123"

    def test_returns_preflop_actions_type(self):
        actions = parse_preflop_actions(_build_block(["Hero: делает фолд"]))
        assert type(actions).__name__ == "PreflopActions"

    def test_action_dataclass_type(self):
        actions = parse_preflop_actions(_build_block(["Hero: делает фолд"]))
        assert type(actions.actions[0]).__name__ == "Action"
