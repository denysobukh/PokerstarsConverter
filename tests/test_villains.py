from parser.action_parser import Action
from utils.villains import compute_villains


# ── helpers ────────────────────────────────────────────────────────────


def _fold(player: str) -> Action:
    return Action(player=player, action_type="fold")


def _call(player: str, amount: float = 0.02) -> Action:
    return Action(player=player, action_type="call", amount=amount)


def _raise(player: str, amount: float = 0.06) -> Action:
    return Action(player=player, action_type="raise", amount=amount)


def _bet(player: str, amount: float = 0.03) -> Action:
    return Action(player=player, action_type="bet", amount=amount)


def _check(player: str) -> Action:
    return Action(player=player, action_type="check")


# ── Positions dict (player_name → position_label) ──────────────────────

_POSITIONS = {
    "Hero": "CO",
    "Villain1": "SB",
    "Villain2": "BB",
    "Villain3": "UTG",
    "Villain4": "HJ",
    "Villain5": "BU",
}


class TestHeroFoldsImmediately:
    """When Hero folds first, only SB/BB are listed."""

    def test_hero_folds_first(self):
        actions = [_fold("Hero")]
        assert compute_villains(actions, "Hero", _POSITIONS) == ["SB", "BB"]

    def test_hero_folds_after_one_villain_fold(self):
        """V1 folds, then Hero folds → only SB/BB."""
        actions = [_fold("Villain3"), _fold("Hero")]
        assert compute_villains(actions, "Hero", _POSITIONS) == ["SB", "BB"]

    def test_hero_folds_after_multiple_folds(self):
        actions = [
            _fold("Villain3"),
            _fold("Villain4"),
            _fold("Hero"),
        ]
        assert compute_villains(actions, "Hero", _POSITIONS) == ["SB", "BB"]

    def test_no_blinds_in_positions(self):
        """When positions dict has no SB/BB, return empty."""
        positions = {"Hero": "CO", "Villain1": "UTG"}
        actions = [_fold("Hero")]
        assert compute_villains(actions, "Hero", positions) == []

    def test_only_bb_in_positions(self):
        positions = {"Hero": "BU", "Villain2": "BB"}
        actions = [_fold("Hero")]
        assert compute_villains(actions, "Hero", positions) == ["BB"]


class TestVillainsFoldBeforeHero:
    """Villains who fold before Hero acts are excluded."""

    def test_villain_folds_before_hero_raises(self):
        """V3 folds, Hero raises, V1 calls → only SB listed."""
        actions = [
            _fold("Villain3"),
            _raise("Hero"),
            _call("Villain1"),
        ]
        assert compute_villains(actions, "Hero", _POSITIONS) == ["SB"]

    def test_multiple_villains_fold_before_hero(self):
        actions = [
            _fold("Villain3"),
            _fold("Villain4"),
            _raise("Hero"),
            _call("Villain1"),
            _call("Villain2"),
        ]
        assert set(compute_villains(actions, "Hero", _POSITIONS)) == {"SB", "BB"}

    def test_villain_folds_after_hero_raises(self):
        """V3 folds AFTER Hero raises → V3 is NOT excluded."""
        actions = [
            _raise("Hero"),
            _fold("Villain3"),
            _call("Villain1"),
        ]
        # V3 folded after Hero acted, but V3 didn't voluntarily put chips in
        # So V3 should not be in the list
        assert compute_villains(actions, "Hero", _POSITIONS) == ["SB"]


class TestVoluntaryChipInvestment:
    """Only players who voluntarily put chips in are listed."""

    def test_call_is_voluntary(self):
        actions = [_raise("Hero"), _call("Villain1")]
        assert compute_villains(actions, "Hero", _POSITIONS) == ["SB"]

    def test_raise_is_voluntary(self):
        actions = [_raise("Hero"), _raise("Villain1")]
        assert compute_villains(actions, "Hero", _POSITIONS) == ["SB"]

    def test_bet_is_voluntary(self):
        actions = [_check("Hero"), _bet("Villain1")]
        assert compute_villains(actions, "Hero", _POSITIONS) == ["SB"]

    def test_fold_is_not_voluntary(self):
        """A player who only folds never voluntarily puts chips in."""
        actions = [_raise("Hero"), _fold("Villain1")]
        assert compute_villains(actions, "Hero", _POSITIONS) == []

    def test_check_is_not_voluntary(self):
        """A player who only checks never voluntarily puts chips in."""
        actions = [_check("Hero"), _check("Villain1")]
        assert compute_villains(actions, "Hero", _POSITIONS) == []


class TestMultipleVillains:
    """Multiple villains with mixed actions."""

    def test_two_villains_invest(self):
        actions = [
            _raise("Hero"),
            _call("Villain1"),
            _call("Villain2"),
        ]
        result = compute_villains(actions, "Hero", _POSITIONS)
        assert set(result) == {"SB", "BB"}

    def test_three_villains_one_folds_early(self):
        """V3 folds before Hero, V1 and V2 call after Hero raises."""
        actions = [
            _fold("Villain3"),
            _raise("Hero"),
            _call("Villain1"),
            _call("Villain2"),
        ]
        result = compute_villains(actions, "Hero", _POSITIONS)
        assert set(result) == {"SB", "BB"}

    def test_villain_raises_then_another_calls(self):
        actions = [
            _raise("Villain1"),
            _raise("Hero"),
            _call("Villain1"),
            _call("Villain2"),
        ]
        result = compute_villains(actions, "Hero", _POSITIONS)
        assert set(result) == {"SB", "BB"}


class TestEdgeCases:
    """Edge cases and corner scenarios."""

    def test_empty_actions(self):
        assert compute_villains([], "Hero", _POSITIONS) == []

    def test_hero_only_player(self):
        """Only Hero acts, no villains."""
        actions = [_raise("Hero")]
        assert compute_villains(actions, "Hero", _POSITIONS) == []

    def test_hero_never_acts(self):
        """Hero has no actions in the list."""
        actions = [_fold("Villain1"), _fold("Villain2")]
        assert compute_villains(actions, "Hero", _POSITIONS) == []

    def test_villain_not_in_positions(self):
        """Villain name not in positions dict → skipped."""
        actions = [_raise("Hero"), _call("UnknownPlayer")]
        assert compute_villains(actions, "Hero", _POSITIONS) == []

    def test_all_villains_fold_after_hero(self):
        """All villains fold after Hero acts → no one invested."""
        actions = [
            _raise("Hero"),
            _fold("Villain1"),
            _fold("Villain2"),
        ]
        assert compute_villains(actions, "Hero", _POSITIONS) == []

    def test_villain_calls_before_and_after_hero(self):
        """Villain limps, Hero raises, Villain calls again."""
        actions = [
            _call("Villain1"),
            _raise("Hero"),
            _call("Villain1"),
        ]
        assert compute_villains(actions, "Hero", _POSITIONS) == ["SB"]
