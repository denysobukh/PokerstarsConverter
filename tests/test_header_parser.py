from parser.header_parser import (
    HandHeader,
    SeatInfo,
    _extract_button_seat,
    _extract_seats,
    _extract_stakes,
    parse_header,
)

# ── helpers ─────────────────────────────────────────────────────────────


def _build_block(
    sb: str = "0.01",
    bb: str = "0.02",
    button_seat: int = 1,
    seats: str = "",
) -> str:
    """Build a minimal hand block with configurable header values."""
    return (
        f"Раздача PokerStars №99999:  Холдем Безлимитный (${sb}/${bb} USD) - 03.05.2026 18:47:49 EET\n"
        f"Стол 'Test' 6-max Баттон на месте №{button_seat}\n"
        f"{seats}"
    )


def _seat_line(num: int, name: str, stack: float) -> str:
    return f"Место {num}: {name} (${stack:.2f} фишек)\n"


# ── Stakes extraction ──────────────────────────────────────────────────


class TestExtractStakes:
    def test_standard_nlt2(self):
        block = _build_block()
        assert _extract_stakes(block) == (0.01, 0.02)

    def test_higher_stakes(self):
        block = _build_block(sb="0.05", bb="0.10")
        assert _extract_stakes(block) == (0.05, 0.10)

    def test_decimal_stakes(self):
        block = _build_block(sb="0.15", bb="0.30")
        assert _extract_stakes(block) == (0.15, 0.30)

    def test_missing_stakes_returns_zeros(self):
        block = "some random text without stakes"
        assert _extract_stakes(block) == (0.0, 0.0)

    def test_empty_block_returns_zeros(self):
        assert _extract_stakes("") == (0.0, 0.0)


# ── Button seat extraction ────────────────────────────────────────────


class TestExtractButtonSeat:
    def test_button_seat_1(self):
        assert _extract_button_seat(_build_block(button_seat=1)) == 1

    def test_button_seat_6(self):
        assert _extract_button_seat(_build_block(button_seat=6)) == 6

    def test_button_seat_3(self):
        assert _extract_button_seat(_build_block(button_seat=3)) == 3

    def test_missing_button_returns_zero(self):
        assert _extract_button_seat("no button info here") == 0

    def test_empty_block_returns_zero(self):
        assert _extract_button_seat("") == 0


# ── Seat extraction ───────────────────────────────────────────────────


class TestExtractSeats:
    def test_full_six_player_table(self):
        seats_text = "".join(
            _seat_line(i, f"Player{i}", 10.0 + i * 0.1) for i in range(1, 7)
        )
        block = _build_block(seats=seats_text)
        seats = _extract_seats(block)
        assert len(seats) == 6
        assert seats[1].name == "Player1"
        assert seats[1].stack == 10.1
        assert seats[6].name == "Player6"
        assert seats[6].stack == 10.6

    def test_gaps_in_seat_numbering(self):
        # Seats 1, 3, 4, 5, 6 — seat 2 is empty
        seats_text = (
            _seat_line(1, "A", 5.0)
            + _seat_line(3, "B", 6.0)
            + _seat_line(4, "C", 7.0)
            + _seat_line(5, "D", 8.0)
            + _seat_line(6, "E", 9.0)
        )
        block = _build_block(seats=seats_text)
        seats = _extract_seats(block)
        assert len(seats) == 5
        assert 2 not in seats
        assert seats[3].name == "B"

    def test_two_players(self):
        seats_text = _seat_line(1, "Hero", 20.0) + _seat_line(2, "Villain", 15.0)
        block = _build_block(seats=seats_text)
        seats = _extract_seats(block)
        assert len(seats) == 2
        assert seats[1].stack == 20.0
        assert seats[2].stack == 15.0

    def test_single_player(self):
        seats_text = _seat_line(4, "Lone", 100.0)
        block = _build_block(seats=seats_text)
        seats = _extract_seats(block)
        assert len(seats) == 1
        assert seats[4].name == "Lone"

    def test_no_seats(self):
        block = _build_block()
        assert _extract_seats(block) == {}

    def test_preserves_exact_stack_value(self):
        seats_text = _seat_line(1, "P", 1.76)
        block = _build_block(seats=seats_text)
        assert _extract_seats(block)[1].stack == 1.76

    def test_seat_info_dataclass_fields(self):
        seats_text = _seat_line(3, "X", 42.5)
        block = _build_block(seats=seats_text)
        info = _extract_seats(block)[3]
        assert info.seat_number == 3
        assert info.name == "X"
        assert info.stack == 42.5


# ── Full parse_header integration ─────────────────────────────────────


class TestParseHeader:
    def test_full_block(self):
        seats_text = (
            _seat_line(1, "Hero", 10.0)
            + _seat_line(2, "V1", 8.0)
            + _seat_line(3, "V2", 12.0)
        )
        block = _build_block(sb="0.05", bb="0.10", button_seat=2, seats=seats_text)
        header = parse_header(block)

        assert isinstance(header, HandHeader)
        assert header.sb == 0.05
        assert header.bb == 0.10
        assert header.button_seat == 2
        assert len(header.seats) == 3
        assert header.seats[1].name == "Hero"

    def test_returns_hand_header_type(self):
        block = _build_block()
        header = parse_header(block)
        assert type(header).__name__ == "HandHeader"

    def test_empty_block_defaults(self):
        header = parse_header("")
        assert header.sb == 0.0
        assert header.bb == 0.0
        assert header.button_seat == 0
        assert header.seats == {}

    def test_sample_file_hand1(self):
        """Verify parsing against actual sample file hand #1 structure."""
        block = (
            "Раздача PokerStars №260679494130:  Холдем Безлимитный ($0.01/$0.02 USD) - 03.05.2026 18:47:49 EET\n"
            "Стол 'Azelfafage IV' 6-max Баттон на месте №1\n"
            "Место 1: Avviee ($1.76 фишек)\n"
            "Место 2: Nakamurastars ($2.01 фишек)\n"
            "Место 3: jonnyjm ($4 фишек)\n"
            "Место 4: mdSz ($2.06 фишек)\n"
            "Место 5: Dragon1248 ($2.24 фишек)\n"
            "Место 6: Danilloo93 ($2 фишек)\n"
        )
        header = parse_header(block)
        assert header.sb == 0.01
        assert header.bb == 0.02
        assert header.button_seat == 1
        assert len(header.seats) == 6
        assert header.seats[1].name == "Avviee"
        assert header.seats[1].stack == 1.76
        assert header.seats[3].stack == 4.0
        assert header.seats[6].name == "Danilloo93"
