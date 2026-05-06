from __future__ import annotations

# Standard pot fractions and their notation labels
_FRACTION_LABELS = {
    1 / 3: "1/3",
    1 / 2: "1/2",
    2 / 3: "2/3",
    3 / 4: "3/4",
    1.0: "pot",
}

# ±5% tolerance window for fraction matching
_TOLERANCE = 0.05


def quantize_size(
    bet_amount: float,
    pot_before: float,
    bb: float,
    eff_stack_bb: int,
    is_all_in: bool = False,
) -> str:
    """Convert a raw bet amount to fraction-of-pot or Xbb notation.

    *bet_amount* — the actual amount wagered.
    *pot_before* — pot size before this bet is added.
    *bb* — big blind amount.
    *eff_stack_bb* — effective stack in big blinds.
    *is_all_in* — whether this action is an all-in.

    Returns:
        - Fraction label (e.g. ``"1/3"``, ``"pot"``) if within ±5% tolerance.
        - ``"Xbb"`` rounded to 1 decimal if no fraction matches.
        - ``""`` if all-in matches the effective stack.
        - ``"Xbb"`` if all-in is shorter than effective stack.
    """
    # ── All-in handling ────────────────────────────────────────────────
    if is_all_in:
        eff_amount = eff_stack_bb * bb
        # Match within half a BB to account for rounding/chip denominations
        if abs(bet_amount - eff_amount) <= bb * 0.5:
            return ""
        # All-in for less → include size
        return _format_bb(bet_amount, bb)

    # ── Fraction matching ──────────────────────────────────────────────
    if pot_before <= 0:
        return _format_bb(bet_amount, bb)

    ratio = bet_amount / pot_before

    for frac, label in _FRACTION_LABELS.items():
        if abs(ratio - frac) <= _TOLERANCE:
            return label

    # ── Fallback to exact Xbb ──────────────────────────────────────────
    return _format_bb(bet_amount, bb)


def _format_bb(amount: float, bb: float) -> str:
    """Return amount formatted as ``Xbb`` rounded to 1 decimal place."""
    if bb <= 0:
        return ""
    return f"{round(amount / bb, 1)}bb"
