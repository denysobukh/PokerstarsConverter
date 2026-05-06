from pokerstars_converter.utils.betsize import quantize_size


class TestFractionMatch:
    """Standard pot fractions should map to their labels."""

    def test_one_third_pot(self):
        assert quantize_size(33.33, 100.0, 1.0, 100) == "1/3"

    def test_half_pot(self):
        assert quantize_size(50.0, 100.0, 1.0, 100) == "1/2"

    def test_two_thirds_pot(self):
        assert quantize_size(66.67, 100.0, 1.0, 100) == "2/3"

    def test_three_quarters_pot(self):
        assert quantize_size(75.0, 100.0, 1.0, 100) == "3/4"

    def test_pot_size(self):
        assert quantize_size(100.0, 100.0, 1.0, 100) == "pot"


class TestToleranceWindow:
    """Bets within ±5% of a fraction should still match that fraction."""

    def test_within_5_percent_high(self):
        """1/3 of 100 is 33.33. 35.0 is within +5% tolerance."""
        assert quantize_size(35.0, 100.0, 1.0, 100) == "1/3"

    def test_within_5_percent_low(self):
        """31.0 is within -5% tolerance of 1/3 pot."""
        assert quantize_size(31.0, 100.0, 1.0, 100) == "1/3"

    def test_edge_of_window_inclusive(self):
        """Ratio exactly at +5% boundary should still match."""
        # 1/3 + 0.05 = 0.38333... → 38.33
        assert quantize_size(38.33, 100.0, 1.0, 100) == "1/3"

    def test_outside_window_fallback(self):
        """Ratio at +6% should fall back to Xbb."""
        # 1/3 + 0.06 = 0.39333... → 39.33
        assert quantize_size(39.33, 100.0, 1.0, 100) == "39.3bb"


class TestNoMatchFallback:
    """Bets that don't match any fraction should return Xbb."""

    def test_arbitrary_size(self):
        assert quantize_size(40.0, 100.0, 1.0, 100) == "40.0bb"

    def test_small_bet(self):
        assert quantize_size(5.0, 100.0, 1.0, 100) == "5.0bb"

    def test_xbb_rounding(self):
        """44.0 chips with bb=2.0 → 22.0bb (outside fraction tolerance)."""
        assert quantize_size(44.0, 100.0, 2.0, 100) == "22.0bb"

    def test_zero_pot_fallback(self):
        """When pot_before is 0, cannot compute ratio → fallback to Xbb."""
        assert quantize_size(10.0, 0.0, 1.0, 100) == "10.0bb"


class TestAllIn:
    """All-in size handling per notation rules."""

    def test_all_in_eff_stack_omit_size(self):
        """All-in matching effective stack → empty string."""
        assert quantize_size(100.0, 100.0, 1.0, 100, is_all_in=True) == ""

    def test_all_in_eff_stack_with_rounding(self):
        """All-in within 0.5 BB of eff stack → empty string."""
        assert quantize_size(99.5, 100.0, 1.0, 100, is_all_in=True) == ""

    def test_all_in_less_include_size(self):
        """All-in shorter than effective stack → include size."""
        assert quantize_size(50.0, 100.0, 1.0, 100, is_all_in=True) == "50.0bb"

    def test_all_in_less_matches_fraction(self):
        """All-in for less that happens to be 1/2 pot → still shows size."""
        assert quantize_size(50.0, 100.0, 1.0, 100, is_all_in=True) == "50.0bb"

    def test_all_in_greater_than_eff(self):
        """All-in larger than eff stack (e.g. side pot) → show size."""
        assert quantize_size(150.0, 100.0, 1.0, 100, is_all_in=True) == "150.0bb"


class TestEdgeCases:
    """Boundary and degenerate conditions."""

    def test_zero_bb(self):
        """bb=0 should return empty string to avoid division by zero."""
        assert quantize_size(10.0, 100.0, 0.0, 100) == ""

    def test_negative_pot(self):
        """Negative pot (shouldn't happen) → fallback to Xbb."""
        assert quantize_size(10.0, -50.0, 1.0, 100) == "10.0bb"

    def test_exact_half_bb_rounding(self):
        """2.5bb should format as 2.5bb, not 2.50bb."""
        assert quantize_size(2.5, 100.0, 1.0, 100) == "2.5bb"

    def test_fraction_preference_over_xbb(self):
        """If within tolerance, fraction wins even if Xbb is cleaner."""
        assert quantize_size(34.0, 100.0, 1.0, 100) == "1/3"
