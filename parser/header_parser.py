from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SeatInfo:
    seat_number: int
    name: str
    stack: float


@dataclass
class HandHeader:
    sb: float
    bb: float
    button_seat: int
    seats: dict[int, SeatInfo]


_LINE_STAKES_RE = re.compile(r'\(\$([0-9.]+)/\$([0-9.]+)\s')
_LINE_BUTTON_RE = re.compile(r'Баттон на месте №(\d+)')
_LINE_SEAT_RE = re.compile(
    r'Место\s+(\d+):\s+(.+?)\s+\(\$([0-9.]+)\s+фишек\)'
)


def parse_header(block: str) -> HandHeader:
    """Extract stakes, button seat, and seated players from a raw hand block."""
    sb, bb = _extract_stakes(block)
    button_seat = _extract_button_seat(block)
    seats = _extract_seats(block)
    return HandHeader(sb=sb, bb=bb, button_seat=button_seat, seats=seats)


# ── helpers ────────────────────────────────────────────────────────────


def _extract_stakes(block: str) -> tuple[float, float]:
    """Return (sb, bb) from the first line that contains stakes info."""
    for line in block.splitlines():
        m = _LINE_STAKES_RE.search(line)
        if m:
            return float(m.group(1)), float(m.group(2))
    return 0.0, 0.0


def _extract_button_seat(block: str) -> int:
    """Return the button seat number."""
    for line in block.splitlines():
        m = _LINE_BUTTON_RE.search(line)
        if m:
            return int(m.group(1))
    return 0


def _extract_seats(block: str) -> dict[int, SeatInfo]:
    """Return {seat_number: SeatInfo} for every seated player."""
    seats: dict[int, SeatInfo] = {}
    for line in block.splitlines():
        m = _LINE_SEAT_RE.match(line)
        if m:
            seat_num = int(m.group(1))
            name = m.group(2)
            stack = float(m.group(3))
            seats[seat_num] = SeatInfo(seat_number=seat_num, name=name, stack=stack)
    return seats
