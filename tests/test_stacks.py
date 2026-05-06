from pokerstars_converter.utils.stacks import compute_eff_stack_bb


class TestComputeEffStackBB:
    """Tests for effective stack computation in big blinds."""

    # ── basic cases ────────────────────────────────────────────────────

    def test_exact_division(self):
        """Hero 10bb, villain 12bb, bb=1 → eff=10."""
        assert compute_eff_stack_bb(10.0, [12.0], 1.0) == 10

    def test_villain_is_shorter(self):
        """Hero 20bb, villain 15bb → eff=15."""
        assert compute_eff_stack_bb(20.0, [15.0], 1.0) == 15

    def test_hero_is_shorter(self):
        """Hero 8bb, villain 100bb → eff=8."""
        assert compute_eff_stack_bb(8.0, [100.0], 1.0) == 8

    def test_equal_stacks(self):
        """Both 50bb → eff=50."""
        assert compute_eff_stack_bb(50.0, [50.0], 1.0) == 50

    # ── floor rounding ─────────────────────────────────────────────────

    def test_floor_rounding(self):
        """10.9bb → 10 (floor)."""
        assert compute_eff_stack_bb(10.9, [20.0], 1.0) == 10

    def test_floor_rounding_small_remainder(self):
        """75.5bb → 75."""
        assert compute_eff_stack_bb(75.5, [100.0], 1.0) == 75

    def test_floor_rounding_large_remainder(self):
        """99.99bb → 99."""
        assert compute_eff_stack_bb(99.99, [200.0], 1.0) == 99

    # ── multiple villains ──────────────────────────────────────────────

    def test_multiple_villains_shortest_wins(self):
        """min(hero=100, v1=80, v2=60, v3=90) → 60."""
        assert compute_eff_stack_bb(100.0, [80.0, 60.0, 90.0], 1.0) == 60

    def test_multiple_villains_hero_shortest(self):
        """min(hero=30, v1=80, v2=60) → 30."""
        assert compute_eff_stack_bb(30.0, [80.0, 60.0], 1.0) == 30

    # ── no villains ────────────────────────────────────────────────────

    def test_no_villains(self):
        """Empty villain list → hero's stack."""
        assert compute_eff_stack_bb(100.0, [], 1.0) == 100

    def test_no_villains_with_floor(self):
        """Empty villain list with non-round stack."""
        assert compute_eff_stack_bb(100.7, [], 1.0) == 100

    # ── real stakes ────────────────────────────────────────────────────

    def test_nlt2_stakes(self):
        """$0.01/$0.02, hero $2.00, villain $1.50 → 75bb."""
        assert compute_eff_stack_bb(2.00, [1.50], 0.02) == 75

    def test_nlt5_stakes(self):
        """$0.02/$0.05, hero $5.00, villain $10.00 → 100bb."""
        assert compute_eff_stack_bb(5.00, [10.00], 0.05) == 100

    def test_nlt1_stakes(self):
        """$0.005/$0.01, hero $1.00, villain $0.75 → 75bb."""
        assert compute_eff_stack_bb(1.00, [0.75], 0.01) == 75

    # ── edge cases ─────────────────────────────────────────────────────

    def test_zero_bb(self):
        """bb=0 → return 0 to avoid division by zero."""
        assert compute_eff_stack_bb(100.0, [50.0], 0.0) == 0

    def test_zero_hero_stack(self):
        """Hero has 0 chips → eff=0."""
        assert compute_eff_stack_bb(0.0, [100.0], 1.0) == 0

    def test_zero_villain_stack(self):
        """Villain has 0 chips → eff=0."""
        assert compute_eff_stack_bb(100.0, [0.0], 1.0) == 0

    def test_fractional_bb(self):
        """bb=0.025, hero=1.00, villain=2.00 → 40bb."""
        assert compute_eff_stack_bb(1.00, [2.00], 0.025) == 40
