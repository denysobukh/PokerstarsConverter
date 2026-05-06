# PokerStars Converter

[![CI](https://github.com/denysobukh/PokerstarsConverter/actions/workflows/ci.yml/badge.svg)](https://github.com/denysobukh/PokerstarsConverter/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Python CLI tool that converts PokerStars hand-history logs (Russian locale) into compact factual poker notation.

<details>
  <summary>Sample input (click to expand)</summary>

```text
*********** №1 **************
Раздача PokerStars №260693414028:  Холдем Безлимитный ($0.01/$0.02 USD) - 04.05.2026 21:35:18 EET [04.05.2026 14:35:18 ВВ]
Стол 'Agelaos V' 6-max Баттон на месте №4
Место 1: weslei418 ($0.89 фишек)
Место 2: Hountex ($2.18 фишек)
Место 3: KA55o ($2.69 фишек)
Место 4: emo357 ($2.04 фишек)
Место 5: Avviee ($0.80 фишек)
Место 6: jonnyjm ($3.79 фишек)
Avviee: ставит малый блайнд $0.01
jonnyjm: ставит большой блайнд $0.02
*** ЗАКРЫТЫЕ КАРТЫ ***
Карты Avviee [2d Th]
weslei418: делает колл $0.02
Hountex: делает рейз $0.06 $0.08
KA55o: делает фолд
emo357: делает колл $0.08
Avviee: делает фолд
jonnyjm: делает фолд
weslei418: делает колл $0.06
*** ФЛОП *** [7d 3c Qc]
weslei418: делает бет $0.04
Hountex: делает колл $0.04
Avviee покидает стол
emo357: делает колл $0.04
*** ТЕРН *** [7d 3c Qc] [Jd]
weslei418: делает бет $0.08
Hountex: делает колл $0.08
emo357: делает фолд
*** РИВЕР *** [7d 3c Qc Jd] [4h]
weslei418: делает чек
Hountex: делает бет $0.78
weslei418: делает колл $0.69 и олл-ин
Неуравненная ставка ($0.09) возвращается игроку Hountex
*** ВСКРЫТИЕ КАРТ ***
Hountex: открывает [Js Jc] (тройку [валеты])
weslei418: открывает [Qd Kc] (пару [дамы])
Hountex получил $1.83 ( банк)
*** ИТОГ ***
Общий банк $1.93 | Доля $0.10
Борд [7d 3c Qc Jd 4h]
Место 1: weslei418 открыл [Qd Kc] и проиграл , собрав пару [дамы]
Место 2: Hountex открыл [Js Jc] и выиграл ($1.83) , собрав тройку [валеты]
Место 3: KA55o сделал фолд до Флоп (не ставил)
Место 4: emo357 (баттон) сделал фолд на Терн
Место 5: Avviee (малый блайнд) сделал фолд до Флоп
Место 6: jonnyjm (большой блайнд) сделал фолд до Флоп
```
</details>

<details>
  <summary>Sample output (click to expand)</summary>

```text
Hand#1
2dTh SB 40bb vs SB, BB

PF: UTG c / HJ r 4.0bb / CO f / BU c / SB f / BB f / UTG c
F 7d3cQc: UTG b 2.0bb / HJ c / BU c
T Jd: UTG b 4.0bb / HJ c / BU f
R 4h: UTG x / HJ b 39.0bb / UTG c

SD: HJ JsJc = set
SD: UTG QdKc = pair
Result: fold
```
</details>

## Install With uv

From a GitHub checkout:

```bash
git clone https://github.com/denysobukh/PokerstarsConverter.git
cd PokerStarsConverter
uv sync
uv run pokerstars-converter doc/sample_input.txt
```

Install it as a global uv tool:

```bash
uv tool install git+https://github.com/denysobukh/PokerstarsConverter.git
pokerstars-converter input_file.txt
```

For local development:

```bash
uv run pytest
```

## Usage

```bash
pokerstars-converter input_file.txt
pokerstars-converter < input_file.txt
pbpaste | pokerstars-converter

python converter.py input_file.txt
python converter.py < input_file.txt
pbpaste | python converter.py
```

Input can be provided as a filename argument or via stdin. Output is written to stdout: one hand block per hand, separated by a blank line. Hands where Hero is not seated are silently skipped. The `converter.py` commands are kept as source-checkout compatibility shims; installed users should prefer `pokerstars-converter`.

## Architecture

The pipeline flows through three layers:

```
converter.py (orchestration)
  │
  ├── src/pokerstars_converter/parser/   — raw text → structured data
  │     hand_splitter    Split file into hand blocks
  │     header_parser    Extract stakes, seats, button
  │     hero_parser      Identify Hero and hole cards
  │     position_mapper  Seat number → table position
  │     action_parser    Parse fold/call/raise/bet/check
  │     street_parser    Parse flop/turn/river boards + actions
  │     showdown_parser  Parse showdown cards + win/loss outcome
  │     models           Dataclasses (Hand, HandHeader, etc.)
  │
  ├── src/pokerstars_converter/utils/    — derived computations
  │     stacks     Effective stack in big blinds
  │     villains   Determine villain list for header
  │     betsize    Quantize bet sizes to fraction-of-pot or Xbb
  │
  └── src/pokerstars_converter/formatter.py — Hand object → compact notation string
```

## Key Design Decisions

- **Russian-only input**: All regex patterns match Russian PokerStars keywords.
- **Hero-centric**: Hands without Hero's hole cards are skipped entirely.
- **Position mapping**: 6-max algorithm; BU is always used (never BTN).
- **Raise parsing**: Two-number format (`$X $Y`) uses `$Y` (total bet).
- **Bet quantization**: ±5% tolerance for standard pot fractions (1/3, 1/2, 2/3, 3/4, pot).

---

## Module Documentation

### `converter.py`

**Purpose:** Main entry point and orchestration module. Reads input, runs the full parse pipeline, and prints formatted output.

**Dependencies:**
- Internal: `pokerstars_converter.parser.hand_splitter`, `pokerstars_converter.parser.header_parser`, `pokerstars_converter.parser.hero_parser`, `pokerstars_converter.parser.position_mapper`, `pokerstars_converter.parser.action_parser`, `pokerstars_converter.parser.street_parser`, `pokerstars_converter.parser.showdown_parser`, `pokerstars_converter.parser.models`, `pokerstars_converter.utils.stacks`, `pokerstars_converter.utils.villains`, `pokerstars_converter.formatter`
- External: `sys`

#### Functions

```python
def parse_hand(block: str) -> Hand | None:
```

* Description: Parses a single raw hand block into a structured `Hand` object. Returns `None` if Hero is not present.
* Parameters:
  * `block` (str): Raw text of one hand, from header through summary.
* Returns:
  * `Hand | None`: Fully populated `Hand`, or `None` to signal skip.
* Side effects: None.

The function performs: header extraction, hero identification, position mapping, preflop action parsing, villain computation, effective stack calculation, post-flop street parsing, and showdown parsing.

```python
def main():
```

* Description: CLI entry point. Reads a file argument or stdin, splits hands, parses each, formats output, prints to stdout.
* Parameters: None (reads `sys.argv` and, when no file argument is present, `sys.stdin`).
* Returns: None.
* Side effects: Prints formatted hands to stdout; exits with code 1 on missing input or file-not-found.
* Raises: `SystemExit` on usage error or file I/O failure.

---

### `formatter.py`

**Purpose:** Converts a parsed `Hand` object into the compact notation string format.

**Dependencies:**
- Internal: `pokerstars_converter.parser.action_parser.Action`, `pokerstars_converter.parser.models.Hand`, `pokerstars_converter.utils.betsize.quantize_size`

#### Constants

```python
_ACTION_SYMBOLS: dict[str, str]
```

* Maps action type strings to notation symbols: `fold→f`, `check→x`, `call→c`, `bet→b`, `raise→r`.

#### Functions

```python
def format_hand(hand: Hand, hand_number: int) -> str:
```

* Description: Assembles a `Hand` into the multi-line notation block.
* Parameters:
  * `hand` (Hand): Parsed hand data.
  * `hand_number` (int): Sequential hand number for output label.
* Returns:
  * `str`: Formatted hand block with header, streets, optional showdown, and result.

Output structure:
1. `Hand#N`
2. Hero cards, position, effective stack, villain positions
3. `PF:` line (preflop actions)
4. `F`, `T`, `R` lines (post-flop streets, if present)
5. `SD:` lines (showdown, if applicable)
6. `Result:` line

```python
def _format_actions(actions: list[Action], pos_map: dict[str, str], bb: float, eff_bb: int) -> str:
```

* Description: Converts a list of `Action` objects into a single street notation string.
* Parameters:
  * `actions` (list[Action]): Actions for one street.
  * `pos_map` (dict[str, str]): Player name → position label mapping.
  * `bb` (float): Big blind amount in dollars.
  * `eff_bb` (int): Effective stack in big blinds.
* Returns:
  * `str`: Space-separated action tokens joined by ` / `.

All-in actions use `a` symbol; bet/raise actions include quantized size; fold/check/call are symbol-only.

---

### `src/pokerstars_converter/parser/models.py`

**Purpose:** Dataclasses that represent parsed poker hand structures.

**Dependencies:**
- Internal: `pokerstars_converter.parser.action_parser.Action`, `pokerstars_converter.parser.header_parser.HandHeader`, `pokerstars_converter.parser.showdown_parser.ShowdownData`, `pokerstars_converter.parser.street_parser.StreetData`
- External: `dataclasses`

#### Classes

```python
@dataclass
class Hand:
```

* Description: Aggregated parsed data for a single poker hand.
* Responsibilities:
  * Holds all parsed components for one hand in a single object.
  * Passed to `formatter.format_hand()` for output generation.
* Key attributes:
  * `header` (HandHeader): Stakes, seats, button seat.
  * `hero_name` (str): Name of the hero player.
  * `hero_cards` (str): Formatted hole card string (e.g. `AdTd`).
  * `hero_position` (str): Table position label (e.g. `CO`, `BU`).
  * `eff_stack_bb` (int): Effective stack in big blinds (floored).
  * `villain_positions` (list[str]): Position labels of relevant villains.
  * `position_map` (dict[str, str]): Player name → position label.
  * `preflop_actions` (list[Action]): Preflop action list.
  * `street_data` (StreetData | None): Post-flop board + actions.
  * `showdown` (ShowdownData | None): Showdown cards and result.

---

### `src/pokerstars_converter/parser/hand_splitter.py`

**Purpose:** Splits a raw PokerStars export file into individual hand blocks.

**Dependencies:**
- External: `re`

#### Constants

```python
HAND_SEPARATOR_RE: re.Pattern
```

* Regex matching the hand separator line: `*********** №N **************`.

```python
FOUR_NEWLINES_RE: re.Pattern
```

* Regex matching 4+ consecutive newlines, used to trim trailing whitespace from the last hand block.

#### Functions

```python
def split_hands(text: str) -> list[str]:
```

* Description: Splits raw export text into a list of individual hand block strings.
* Parameters:
  * `text` (str): Full content of a PokerStars export file.
* Returns:
  * `list[str]`: List of stripped hand block strings. Empty list for empty input.
* Side effects: None.

Skips non-hand blocks and trims trailing whitespace from the final block.

```python
def _is_hand_block(text: str) -> bool:
```

* Description: Checks whether a text block starts with a valid hand record header.
* Parameters:
  * `text` (str): Text to check.
* Returns:
  * `bool`: `True` if text begins with `Раздача PokerStars №`.

---

### `src/pokerstars_converter/parser/header_parser.py`

**Purpose:** Extracts hand metadata (stakes, button seat, player roster) from a raw hand block.

**Dependencies:**
- External: `re`, `dataclasses`

#### Classes

```python
@dataclass
class SeatInfo:
```

* Description: Information about a single seated player.
* Key attributes:
  * `seat_number` (int): Seat position number.
  * `name` (str): Player display name.
  * `stack` (float): Chip count in dollars (before blinds posted).

```python
@dataclass
class HandHeader:
```

* Description: Metadata for a single hand.
* Key attributes:
  * `sb` (float): Small blind amount.
  * `bb` (float): Big blind amount.
  * `button_seat` (int): Seat number of the button.
  * `seats` (dict[int, SeatInfo]): Seat number → player info mapping.

#### Functions

```python
def parse_header(block: str) -> HandHeader:
```

* Description: Extracts stakes, button seat, and seated players from a raw hand block.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `HandHeader`: Populated header object.

```python
def _extract_stakes(block: str) -> tuple[float, float]:
```

* Description: Returns `(sb, bb)` from the stakes line.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `tuple[float, float]`: `(small_blind, big_blind)`. Returns `(0.0, 0.0)` if not found.

```python
def _extract_button_seat(block: str) -> int:
```

* Description: Returns the button seat number.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `int`: Button seat number. Returns `0` if not found.

```python
def _extract_seats(block: str) -> dict[int, SeatInfo]:
```

* Description: Returns a dict of seat number to `SeatInfo` for every seated player.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `dict[int, SeatInfo]`: Seat roster.

---

### `src/pokerstars_converter/parser/hero_parser.py`

**Purpose:** Identifies the hero player and parses hole card notation.

**Dependencies:**
- External: `re`, `dataclasses`

#### Classes

```python
@dataclass
class HeroInfo:
```

* Description: Hero identification data extracted from the `Карты` line.
* Key attributes:
  * `name` (str): Hero's player name.
  * `card1` (str): First hole card (e.g. `Ad`).
  * `card2` (str): Second hole card (e.g. `Td`).

#### Functions

```python
def extract_hero(block: str) -> HeroInfo | None:
```

* Description: Returns `HeroInfo` from the first `Карты` line in the block, or `None` if not found.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `HeroInfo | None`: Hero data, or `None` if no hero cards present.

```python
def _parse_two_cards(raw: str) -> tuple[str, str]:
```

* Description: Splits a raw card string (e.g. `Ad Td`) into two validated card tokens.
* Parameters:
  * `raw` (str): Space-separated card string.
* Returns:
  * `tuple[str, str]`: Two card strings, or `('', '')` if validation fails.

```python
def _normalize_card(token: str) -> str:
```

* Description: Validates a single card token against the rank+suit pattern.
* Parameters:
  * `token` (str): Card string to validate.
* Returns:
  * `str`: Token if valid, empty string otherwise.

```python
def card_rank(card: str) -> str:
```

* Description: Extracts the rank from a card string.
* Parameters:
  * `card` (str): Card string (e.g. `Ad`).
* Returns:
  * `str`: Rank character (e.g. `A`).

```python
def card_suit(card: str) -> str:
```

* Description: Extracts the suit from a card string.
* Parameters:
  * `card` (str): Card string (e.g. `Ad`).
* Returns:
  * `str`: Suit character (`c`, `d`, `h`, or `s`).

```python
def format_hero_cards(card1: str, card2: str) -> str:
```

* Description: Concatenates two card strings into the output notation format.
* Parameters:
  * `card1` (str): First card.
  * `card2` (str): Second card.
* Returns:
  * `str`: Concatenated card string (e.g. `AdTd`).

---

### `src/pokerstars_converter/parser/position_mapper.py`

**Purpose:** Maps seat numbers to table position labels (BU, SB, BB, UTG, HJ, CO) for 6-max tables.

**Dependencies:** None (pure logic).

#### Constants

```python
_POSITIONS_6, _POSITIONS_5, _POSITIONS_4, _POSITIONS_3, _POSITIONS_2: tuple[str, ...]
```

* Position label tuples for each player count. BU, SB, BB are always present; early positions are dropped first for fewer players.

```python
_POSITION_TABLE: dict[int, tuple[str, ...]]
```

* Maps player count (2–6) to the corresponding position tuple.

#### Functions

```python
def assign_positions(button_seat: int, seat_numbers: list[int]) -> dict[int, str]:
```

* Description: Maps each seat number to its table position label.
* Parameters:
  * `button_seat` (int): Seat number holding the button.
  * `seat_numbers` (list[int]): Sorted list of active seat numbers.
* Returns:
  * `dict[int, str]`: Seat number → position label mapping.
* Raises:
  * `ValueError`: If `seat_numbers` is empty or `button_seat` is not in `seat_numbers`.

Algorithm: Starting from the button seat, assigns positions clockwise (ascending seat number, wrapping around).

---

### `src/pokerstars_converter/parser/action_parser.py`

**Purpose:** Parses individual player actions (fold, check, call, raise, bet) from raw hand text.

**Dependencies:**
- External: `re`, `dataclasses`

#### Classes

```python
@dataclass
class Action:
```

* Description: A single parsed player action.
* Key attributes:
  * `player` (str): Player name.
  * `action_type` (str): One of `fold`, `check`, `call`, `raise`, `bet`.
  * `amount` (float): Dollar amount (for call/raise/bet). Default `0.0`.
  * `all_in` (bool): Whether the action includes an all-in suffix. Default `False`.

```python
@dataclass
class PreflopActions:
```

* Description: Container for all preflop actions in a hand.
* Key attributes:
  * `actions` (list[Action]): Ordered list of preflop actions.

#### Functions

```python
def extract_preflop_section(block: str) -> str:
```

* Description: Returns only the lines between the preflop marker (`*** ЗАКРЫТЫЕ КАРТЫ ***`) and the flop marker.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `str`: Newline-joined preflop section lines.

```python
def parse_preflop_actions(block: str) -> PreflopActions:
```

* Description: Parses all player actions in the preflop section of a hand block.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `PreflopActions`: Container with parsed action list.

```python
def _parse_single_action(line: str) -> Action | None:
```

* Description: Attempts to parse one action line against all known patterns.
* Parameters:
  * `line` (str): Single line of hand text.
* Returns:
  * `Action | None`: Parsed action, or `None` for non-action lines.

Pattern matching order (important for correctness): `fold` → `check` → `call_allin` → `call` → `raise_allin` → `raise` → `bet_allin` → `bet`. All-in variants are checked before their non-all-in counterparts.

The raise handler uses `m.group(3)` (the second dollar figure) as the total bet amount.

---

### `src/pokerstars_converter/parser/street_parser.py`

**Purpose:** Parses post-flop board cards and actions for flop, turn, and river streets.

**Dependencies:**
- Internal: `pokerstars_converter.parser.action_parser.Action`, `pokerstars_converter.parser.action_parser._parse_single_action`
- External: `re`, `dataclasses`

#### Classes

```python
@dataclass
class BoardCards:
```

* Description: Board cards parsed from F/T/R section markers.
* Key attributes:
  * `flop` (list[str]): Three flop cards.
  * `turn` (str): Single turn card.
  * `river` (str): Single river card.

```python
@dataclass
class StreetActions:
```

* Description: Actions parsed for each post-flop street.
* Key attributes:
  * `flop` (list[Action]): Flop street actions.
  * `turn` (list[Action]): Turn street actions.
  * `river` (list[Action]): River street actions.

```python
@dataclass
class StreetData:
```

* Description: Complete post-preflop data: board + actions for each street.
* Key attributes:
  * `board` (BoardCards): Board card data.
  * `actions` (StreetActions): Action data per street.

#### Functions

```python
def parse_streets(block: str) -> StreetData:
```

* Description: Parses board cards and actions for flop, turn, and river streets.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `StreetData`: Populated street data (may have empty fields if hand ended early).

```python
def _parse_board_cards(block: str) -> BoardCards:
```

* Description: Extracts flop/turn/river cards from section markers.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `BoardCards`: Populated board card object.

```python
def _extract_flop_cards(block: str) -> list[str]:
```

* Description: Returns flop cards from the `*** ФЛОП ***` line.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `list[str]`: Three card strings, or empty list.

```python
def _extract_turn_card(block: str) -> str:
```

* Description: Returns the single turn card from the `*** ТЕРН ***` line.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `str`: Turn card string, or empty string.

```python
def _extract_river_card(block: str) -> str:
```

* Description: Returns the single river card from the `*** РИВЕР ***` line.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `str`: River card string, or empty string.

```python
def _parse_street_actions(block: str) -> StreetActions:
```

* Description: Parses actions for each post-flop street using section boundary markers.
* Parameters:
  * `block` (str): Raw hand text.
* Returns:
  * `StreetActions`: Actions per street.

```python
def _extract_section_lines(block: str, start: str, stop_markers: list[str]) -> list[str]:
```

* Description: Generic helper that returns action lines between a start marker and any stop marker.
* Parameters:
  * `block` (str): Raw hand text.
  * `start` (str): Start marker substring.
  * `stop_markers` (list[str]): List of stop marker substrings.
* Returns:
  * `list[str]`: Lines between markers.

---

### `src/pokerstars_converter/parser/showdown_parser.py`

**Purpose:** Parses showdown cards, hand names, and win/loss/fold outcome from the summary section.

**Dependencies:**
- External: `re`, `dataclasses`

#### Classes

```python
@dataclass
class ShowdownVillain:
```

* Description: A single villain's showdown information.
* Key attributes:
  * `player` (str): Villain player name.
  * `cards` (list[str]): Shown hole cards.
  * `hand_name` (str): English hand name (translated from Russian).

```python
@dataclass
class ShowdownData:
```

* Description: Parsed showdown and result data for a hand.
* Key attributes:
  * `villains` (list[ShowdownVillain]): List of villains who showed cards.
  * `result` (str): One of `won`, `lost`, `fold`, `unknown`.

#### Constants

```python
_HAND_NAME_MAP: list[tuple[str, str]]
```

* Russian-to-English hand name mapping table. Entries include: `стрит-флеш→straight flush`, `пару→pair`, `две пары→two pair`, `тройку→set`, `стрит→straight`, `флеш→flush`, `фулл-хаус→full house`, `каретку→quads`, `старшую карту→high card`, `роял-флеш→royal flush`.

#### Functions

```python
def parse_showdown(block: str, hero_name: str) -> ShowdownData | None:
```

* Description: Parses showdown cards, hand names, and win/loss/fold outcome.
* Parameters:
  * `block` (str): Raw hand text.
  * `hero_name` (str): Hero's player name (excluded from villain list).
* Returns:
  * `ShowdownData | None`: Showdown data, or `None` if no showdown and hero did not fold.

```python
def _parse_showdown_villains(block: str, hero_name: str) -> list[ShowdownVillain]:
```

* Description: Extracts each villain's shown cards and hand name from the showdown section.
* Parameters:
  * `block` (str): Raw hand text.
  * `hero_name` (str): Hero's name (skipped in output).
* Returns:
  * `list[ShowdownVillain]`: Villain showdown data.

```python
def _translate_hand_name(raw: str) -> str:
```

* Description: Maps a Russian hand-name fragment to its English equivalent.
* Parameters:
  * `raw` (str): Russian hand name string (may include extra detail in brackets).
* Returns:
  * `str`: English hand name, or `unknown` if no match.

```python
def _parse_result(block: str, hero_name: str) -> str:
```

* Description: Determines hero's outcome from the summary section.
* Parameters:
  * `block` (str): Raw hand text.
  * `hero_name` (str): Hero's player name.
* Returns:
  * `str`: One of `won`, `lost`, `fold`, `unknown`.

Checks for `выиграл` (won), `проиграл` (lost), `сделал фолд` (fold), and `собрал` (collected blinds = won).

```python
def _is_hero_result_line(line: str, hero_name: str) -> bool:
```

* Description: Checks whether a summary line belongs to the hero.
* Parameters:
  * `line` (str): Summary line starting with `Место N:`.
  * `hero_name` (str): Hero's player name.
* Returns:
  * `bool`: `True` if the line's player name matches hero.

---

### `src/pokerstars_converter/utils/stacks.py`

**Purpose:** Computes effective stack depth in big blinds.

**Dependencies:**
- External: `math`

#### Functions

```python
def compute_eff_stack_bb(hero_chips: float, villain_chips: list[float], bb: float) -> int:
```

* Description: Computes effective stack in big blinds, rounded down (floor).
* Parameters:
  * `hero_chips` (float): Hero's chip count in dollars.
  * `villain_chips` (list[float]): List of villain chip counts in dollars.
  * `bb` (float): Big blind amount in dollars.
* Returns:
  * `int`: Effective stack in BB (floored). Returns `0` if `bb <= 0`.

Formula: `floor(min(hero_chips, min(villain_chips)) / bb)`. When `villain_chips` is empty, uses `hero_chips` alone.

---

### `src/pokerstars_converter/utils/villains.py`

**Purpose:** Determines which villain positions appear in the hand header.

**Dependencies:**
- Internal: `pokerstars_converter.parser.action_parser.Action`

#### Functions

```python
def compute_villains(actions: list[Action], hero_name: str, positions: dict[str, str]) -> list[str]:
```

* Description: Determines villain positions for the header line.
* Parameters:
  * `actions` (list[Action]): Ordered list of preflop actions.
  * `hero_name` (str): Hero's player name.
  * `positions` (dict[str, str]): Player name → position label mapping.
* Returns:
  * `list[str]`: Position labels of relevant villains.

Villain criteria:
1. Did not fold before Hero acted preflop, AND
2. Voluntarily put chips in the pot while Hero was still active.

When Hero folds immediately (first legal action), only SB and BB are listed.

```python
def _hero_first_action_index(actions: list[Action], hero_name: str) -> int:
```

* Description: Returns the index of Hero's first action.
* Parameters:
  * `actions` (list[Action]): Ordered action list.
  * `hero_name` (str): Hero's player name.
* Returns:
  * `int`: Index, or `len(actions)` if Hero has no actions.

```python
def _hero_folded_immediately(actions: list[Action], hero_name: str, hero_first_idx: int) -> bool:
```

* Description: Returns `True` when Hero's first legal action is a fold.
* Parameters:
  * `actions` (list[Action]): Ordered action list.
  * `hero_name` (str): Hero's player name.
  * `hero_first_idx` (int): Index of Hero's first action.
* Returns:
  * `bool`.

```python
def _list_blinds(positions: dict[str, str]) -> list[str]:
```

* Description: Returns SB and BB position labels if present in the position map.
* Parameters:
  * `positions` (dict[str, str]): Player name → position label mapping.
* Returns:
  * `list[str]`: List containing `SB` and/or `BB` (in that order).

---

### `src/pokerstars_converter/utils/betsize.py`

**Purpose:** Quantizes raw bet amounts to fraction-of-pot or Xbb notation.

**Dependencies:** None (pure computation).

#### Constants

```python
_FRACTION_LABELS: dict[float, str]
```

* Maps pot fractions to notation labels: `1/3`, `1/2`, `2/3`, `3/4`, `1.0→pot`.

```python
_TOLERANCE: float = 0.05
```

* ±5% tolerance window for fraction matching.

#### Functions

```python
def quantize_size(bet_amount: float, pot_before: float, bb: float, eff_stack_bb: int, is_all_in: bool = False) -> str:
```

* Description: Converts a raw bet amount to fraction-of-pot or Xbb notation.
* Parameters:
  * `bet_amount` (float): Actual amount wagered.
  * `pot_before` (float): Pot size before this bet.
  * `bb` (float): Big blind amount.
  * `eff_stack_bb` (int): Effective stack in big blinds.
  * `is_all_in` (bool): Whether this action is an all-in. Default `False`.
* Returns:
  * `str`: Fraction label (e.g. `1/3`, `pot`), `Xbb` rounded to 1 decimal, or empty string for all-in matching eff stack.

All-in handling: If the all-in amount matches the effective stack within ±0.5 BB, returns empty string (size omitted). Otherwise returns `Xbb`.

Non-all-in: Tests against standard fractions in order. If no fraction matches within ±5%, falls back to `Xbb`.

```python
def _format_bb(amount: float, bb: float) -> str:
```

* Description: Formats an amount as `Xbb` rounded to 1 decimal place.
* Parameters:
  * `amount` (float): Dollar amount.
  * `bb` (float): Big blind amount.
* Returns:
  * `str`: Formatted string (e.g. `2.5bb`). Returns empty string if `bb <= 0`.

---

## Cross-Module Insights

### Data Flow

```
Raw text → split_hands() → [hand blocks]
  → parse_header() → HandHeader
  → extract_hero() → HeroInfo
  → assign_positions() → seat→position map
  → parse_preflop_actions() → PreflopActions
  → compute_villains() → villain position list
  → compute_eff_stack_bb() → effective stack
  → parse_streets() → StreetData
  → parse_showdown() → ShowdownData
  → Hand (aggregated)
  → format_hand() → notation string
```

### Key Abstractions

1. **`Hand` dataclass** (`src/pokerstars_converter/parser/models.py`): Central aggregation object. All parser modules contribute fields; `formatter.py` consumes it.
2. **`Action` dataclass** (`src/pokerstars_converter/parser/action_parser.py`): Shared action representation used by preflop parser, street parser, villain computation, and formatter.
3. **Section extraction pattern**: Both `action_parser.py` and `street_parser.py` use a start/stop marker pattern to isolate text sections before parsing.

### Coupling Observations

- `street_parser.py` imports `_parse_single_action` directly from `pokerstars_converter.parser.action_parser` (private cross-module dependency). This is intentional to reuse the action parser for post-flop streets.
- `converter.py` is the sole orchestrator; all other modules are leaf nodes with no inter-dependencies (except the above).
- `formatter.py` depends on `Hand`, `Action`, and `quantize_size` — a clean consumer of parsed data.

---

## Optional Improvements

### Missing Docstrings

- `src/pokerstars_converter/parser/models.py`: `Hand` class has a brief docstring but individual fields are undocumented. Consider per-field docstrings or type-level documentation.
- `src/pokerstars_converter/parser/hero_parser.py`: `_parse_two_cards`, `_normalize_card`, `card_rank`, `card_suit` lack docstrings.
- `src/pokerstars_converter/parser/street_parser.py`: `_split_cards`, `_actions_from_lines`, `_extract_flop_action_lines`, `_extract_turn_action_lines`, `_extract_river_action_lines` lack docstrings.
- `src/pokerstars_converter/parser/showdown_parser.py`: `_parse_showdown_villains`, `_translate_hand_name`, `_parse_result`, `_is_hero_result_line` lack docstrings.
- `src/pokerstars_converter/utils/villains.py`: `_hero_first_action_index`, `_hero_folded_immediately`, `_list_blinds` lack docstrings.
### Type Annotations

- `src/pokerstars_converter/parser/hand_splitter.py`: `_is_hand_block` return type is implicit `bool` (acceptable, but explicit annotation would be consistent).

### Refactoring Suggestions

1. **Duplicate section extraction logic**: `extract_preflop_section` in `action_parser.py` and `_extract_section_lines` in `street_parser.py` implement the same pattern. Consider extracting to a shared utility.
2. **`format_hero_cards` is a pass-through**: The function currently just concatenates `card1 + card2`. The docstring mentions pocket pair vs non-pair formatting rules, but the implementation does not differentiate. Either implement the distinction or remove the misleading docstring.
3. **`_parse_single_action` visibility**: This function is marked private (underscore prefix) but is imported by `street_parser.py`. Consider making it public or creating a shared module for action parsing.
4. **Hard-coded Russian strings**: All regex patterns and string literals are Russian-specific. If English locale support is ever needed, these should be parameterized or abstracted behind a locale configuration.
