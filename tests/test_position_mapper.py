import pytest
from pokerstars_converter.parser.position_mapper import assign_positions


# ── 6 players ──────────────────────────────────────────────────────────


class TestSixPlayers:
    def test_button_seat_1(self):
        """BU=1, SB=2, BB=3, UTG=4, HJ=5, CO=6"""
        result = assign_positions(1, [1, 2, 3, 4, 5, 6])
        assert result == {1: "BU", 2: "SB", 3: "BB", 4: "UTG", 5: "HJ", 6: "CO"}

    def test_button_seat_3(self):
        """BU=3, SB=4, BB=5, UTG=6, HJ=1, CO=2"""
        result = assign_positions(3, [1, 2, 3, 4, 5, 6])
        assert result == {3: "BU", 4: "SB", 5: "BB", 6: "UTG", 1: "HJ", 2: "CO"}

    def test_button_seat_6(self):
        """BU=6, SB=1, BB=2, UTG=3, HJ=4, CO=5"""
        result = assign_positions(6, [1, 2, 3, 4, 5, 6])
        assert result == {6: "BU", 1: "SB", 2: "BB", 3: "UTG", 4: "HJ", 5: "CO"}

    def test_button_seat_4(self):
        """BU=4, SB=5, BB=6, UTG=1, HJ=2, CO=3"""
        result = assign_positions(4, [1, 2, 3, 4, 5, 6])
        assert result == {4: "BU", 5: "SB", 6: "BB", 1: "UTG", 2: "HJ", 3: "CO"}


# ── 5 players ──────────────────────────────────────────────────────────


class TestFivePlayers:
    def test_button_seat_1(self):
        """BU=1, SB=2, BB=3, UTG=4, HJ=5"""
        result = assign_positions(1, [1, 2, 3, 4, 5])
        assert result == {1: "BU", 2: "SB", 3: "BB", 4: "UTG", 5: "HJ"}

    def test_button_seat_2(self):
        """BU=2, SB=3, BB=4, UTG=5, HJ=1"""
        result = assign_positions(2, [1, 2, 3, 4, 5])
        assert result == {2: "BU", 3: "SB", 4: "BB", 5: "UTG", 1: "HJ"}

    def test_gapped_seats(self):
        """Seats 1, 3, 4, 5, 6 with button at 3"""
        result = assign_positions(3, [1, 3, 4, 5, 6])
        assert result == {3: "BU", 4: "SB", 5: "BB", 6: "UTG", 1: "HJ"}


# ── 4 players ──────────────────────────────────────────────────────────


class TestFourPlayers:
    def test_button_seat_1(self):
        """BU=1, SB=2, BB=3, UTG=4"""
        result = assign_positions(1, [1, 2, 3, 4])
        assert result == {1: "BU", 2: "SB", 3: "BB", 4: "UTG"}

    def test_button_seat_4(self):
        """BU=4, SB=1, BB=2, UTG=3"""
        result = assign_positions(4, [1, 2, 3, 4])
        assert result == {4: "BU", 1: "SB", 2: "BB", 3: "UTG"}


# ── 3 players ──────────────────────────────────────────────────────────


class TestThreePlayers:
    def test_button_seat_1(self):
        """BU=1, SB=2, BB=3"""
        result = assign_positions(1, [1, 2, 3])
        assert result == {1: "BU", 2: "SB", 3: "BB"}

    def test_button_seat_2(self):
        """BU=2, SB=3, BB=1"""
        result = assign_positions(2, [1, 2, 3])
        assert result == {2: "BU", 3: "SB", 1: "BB"}

    def test_button_seat_3(self):
        """BU=3, SB=1, BB=2"""
        result = assign_positions(3, [1, 2, 3])
        assert result == {3: "BU", 1: "SB", 2: "BB"}


# ── 2 players (heads-up) ──────────────────────────────────────────────


class TestTwoPlayers:
    def test_button_seat_1(self):
        """BU=1, BB=2 (no SB in heads-up)"""
        result = assign_positions(1, [1, 2])
        assert result == {1: "BU", 2: "BB"}

    def test_button_seat_2(self):
        """BU=2, BB=1"""
        result = assign_positions(2, [1, 2])
        assert result == {2: "BU", 1: "BB"}

    def test_gapped_seats(self):
        """Seats 3 and 5 with button at 3"""
        result = assign_positions(3, [3, 5])
        assert result == {3: "BU", 5: "BB"}


# ── Error cases ────────────────────────────────────────────────────────


class TestErrors:
    def test_empty_seats(self):
        with pytest.raises(ValueError, match="No active seats"):
            assign_positions(1, [])

    def test_button_not_in_seats(self):
        with pytest.raises(ValueError, match="Button seat"):
            assign_positions(7, [1, 2, 3])

    def test_button_not_in_seats_unsorted(self):
        with pytest.raises(ValueError, match="Button seat"):
            assign_positions(5, [1, 2, 3, 4])


# ── Property tests ─────────────────────────────────────────────────────


class TestProperties:
    def test_all_seats_mapped(self):
        """Every seat gets exactly one position."""
        seats = [1, 2, 3, 4, 5, 6]
        result = assign_positions(3, seats)
        assert len(result) == len(seats)
        assert set(result.keys()) == set(seats)

    def test_no_duplicate_positions_6(self):
        positions = assign_positions(2, [1, 2, 3, 4, 5, 6]).values()
        assert len(positions) == len(set(positions))

    def test_no_duplicate_positions_3(self):
        positions = assign_positions(1, [1, 2, 3]).values()
        assert len(positions) == len(set(positions))

    def test_button_always_BU(self):
        for btn in [1, 2, 3, 4, 5, 6]:
            result = assign_positions(btn, [1, 2, 3, 4, 5, 6])
            assert result[btn] == "BU"

    def test_unsorted_input_handled(self):
        """Input list doesn't need to be pre-sorted."""
        result = assign_positions(3, [6, 1, 4, 2, 5, 3])
        assert result[3] == "BU"
