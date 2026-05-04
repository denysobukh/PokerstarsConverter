from __future__ import annotations


_POSITIONS_6 = ("BU", "SB", "BB", "UTG", "HJ", "CO")
_POSITIONS_5 = ("BU", "SB", "BB", "UTG", "HJ")
_POSITIONS_4 = ("BU", "SB", "BB", "UTG")
_POSITIONS_3 = ("BU", "SB", "BB")
_POSITIONS_2 = ("BU", "BB")

_POSITION_TABLE = {
    6: _POSITIONS_6,
    5: _POSITIONS_5,
    4: _POSITIONS_4,
    3: _POSITIONS_3,
    2: _POSITIONS_2,
}


def assign_positions(
    button_seat: int,
    seat_numbers: list[int],
) -> dict[int, str]:
    """Map each seat number to its table position label.

    *button_seat* is the seat that has the button.
    *seat_numbers* is the sorted list of active seat numbers.

    Returns {seat_number: position_label}.
    Raises ValueError on invalid input.
    """
    if not seat_numbers:
        raise ValueError("No active seats")
    if button_seat not in seat_numbers:
        raise ValueError(f"Button seat {button_seat} not in active seats")

    n = len(seat_numbers)
    positions = _POSITION_TABLE.get(n, _POSITIONS_6)

    sorted_seats = sorted(seat_numbers)
    button_index = sorted_seats.index(button_seat)

    mapping: dict[int, str] = {}
    for i, label in enumerate(positions):
        seat_index = (button_index + i) % n
        mapping[sorted_seats[seat_index]] = label

    return mapping
