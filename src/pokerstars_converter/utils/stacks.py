from __future__ import annotations

import math


def compute_eff_stack_bb(
    hero_chips: float,
    villain_chips: list[float],
    bb: float,
) -> int:
    """Compute effective stack in big blinds, rounded down (floor).

    Effective stack = min(hero_chips, min(villain_chips)) / bb.
    When villain_chips is empty, uses hero_chips alone.
    """
    if bb <= 0:
        return 0

    if villain_chips:
        eff = min(hero_chips, min(villain_chips))
    else:
        eff = hero_chips

    return int(math.floor(eff / bb))
