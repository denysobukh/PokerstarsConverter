# Implementation Plan

## Stage 1: Project scaffolding + hand splitting

**Goal:** Read raw text, split into individual hand blocks, return list of raw hand strings.

**Deliverables:**
- `parser/hand_splitter.py` — `split_hands(text: str) -> list[str]`
- `tests/test_hand_splitter.py` — verify splitting on `*********** №N **************` separator, trailing/leading whitespace, empty input, single hand, many hands

**Acceptance criteria:**
- `split_hands("")` returns `[]`
- Single hand returns 1 block
- 20-hand sample file returns 20 blocks
- Each block is self-contained (includes header through `*** ИТОГ ***`)

---

## Stage 2: Parse hand header (metadata extraction)

**Goal:** From a raw hand block, extract: stakes (SB/BB), button seat, seated players with chip counts.

**Deliverables:**
- `parser/models.py` — `Player` (name, seat, chips), `HandHeader` (sb, bb, button_seat, players dict) dataclasses
- `parser/header_parser.py` — `parse_header(block: str) -> HandHeader`
- `tests/test_header_parser.py` — parse stakes, button seat, player roster, missing seats (e.g. seat 2 empty), player joining mid-hand ignored

**Acceptance criteria:**
- Correctly parses `$0.01/$0.02` stakes
- Button seat extracted from `Баттон на месте №N`
- All `Место N: Name ($X фишек)` lines parsed with correct seat/name/chips
- Handles gaps in seat numbering (e.g. hand #3 missing seat 2)

---

## Stage 3: Hero identification + hole card parsing

**Goal:** Identify Hero from `Карты [name] [cards]` line in preflop section; parse card notation.

**Deliverables:**
- `parser/models.py` — extend with `Hand` dataclass (hero_name, hero_cards, header, actions, board, showdown, result)
- `parser/hero_parser.py` — `identify_hero(block: str) -> tuple[str, str, str]` returns (name, card1, card2)
- `utils/cards.py` — `format_cards(card1: str, card2: str) -> str` (pocket pair vs suited/offsuit)
- `tests/test_hero_parser.py` — hero found, hero not seated (skip hand), card formatting (pairs, suited, offsuit)

**Acceptance criteria:**
- Hero name matches the `Карты` line
- Cards parsed from `[Ad Td]` format
- `format_cards("Ad", "Ac")` → `"AdAc"`, `format_cards("7d", "7h")` → `"7d7h"`
- Hand with no `Карты [hero]` line for the known hero name is flagged for skip

---

## Stage 4: Position mapping algorithm

**Goal:** Given button seat and list of active seated players, assign position labels.

**Deliverables:**
- `utils/positions.py` — `assign_positions(button_seat: int, seats: list[int]) -> dict[int, str]`
- `tests/test_positions.py` — 2-player (BU+BB), 3-player, 4-player, 5-player, 6-player; button at every seat position

**Acceptance criteria:**
- 6 players: BU → SB → BB → UTG → HJ → CO (clockwise from button)
- 5 players: BU → SB → BB → UTG → HJ (drop CO)
- 4 players: BU → SB → BB → UTG (drop HJ, CO)
- 3 players: BU → SB → BB (drop UTG, HJ, CO)
- 2 players: BU → BB (SB folded/not present; BU posts SB)
- Button at seat 1, 2, 3, 4, 5, 6 all produce correct rotation

---

## Stage 5: Parse preflop actions

**Goal:** Parse fold/call/raise/check actions between `*** ЗАКРЫТЫЕ КАРТЫ ***` and `*** ФЛОП ***` (or end if no flop).

**Deliverables:**
- `parser/models.py` — `Action` dataclass (player_name, action_type, amount, is_allin)
- `parser/action_parser.py` — `parse_actions(block: str, street: str) -> list[Action]`
- `tests/test_action_parser.py` — fold, call, raise (two-number format), check, all-in suffix, BB option check

**Acceptance criteria:**
- `делает фолд` → `Action("fold")`
- `делает колл $X` → `Action("call", amount=X)`
- `делает рейз $X $Y` → `Action("raise", amount=Y)` (total, not increment)
- `делает бет $X` → `Action("bet", amount=X)`
- `делает чек` → `Action("check")`
- `и олл-ин` suffix detected on raise/bet/call
- BB option check (BB checks after everyone else folds/calls preflop) recorded as `x`

---

## Stage 6: Parse postflop streets (flop/turn/river)

**Goal:** Parse board cards and actions for F/T/R streets.

**Deliverables:**
- `parser/street_parser.py` — `parse_postflop(block: str) -> dict[str, tuple[list[str], list[Action]]]` keyed by "flop"/"turn"/"river"
- `tests/test_street_parser.py` — flop 3 cards, turn 1 card, river 1 card; check-check street; bet-fold; all-in on river

**Acceptance criteria:**
- Board cards extracted from `*** ФЛОП *** [c1 c2 c3]`, `*** ТЕРН *** [...] [c4]`, `*** РИВЕР *** [...] [c5]`
- Actions between street markers correctly attributed to street
- Missing streets (e.g. hand ended preflop) return empty

---

## Stage 7: Parse showdown and result

**Goal:** Extract showdown cards, hand names, and win/loss/fold outcome.

**Deliverables:**
- `parser/showdown_parser.py` — `parse_showdown(block: str) -> ShowdownData | None`
- `parser/models.py` — `ShowdownData` (villain_cards, villain_hand_name, hero_wins: win | loss | fold)
- `tests/test_showdown_parser.py` — hero wins, hero loses, hero folds, no showdown (all fold), set vs trips distinction

**Acceptance criteria:**
- `открывает [cards]` lines parsed
- Hand name from Russian text mapped to English: `стрит`→`straight`, `пару`→`pair`, `старшую карту`→`high card`, etc.
- Hero win/loss/fold determined from `выиграл`/`проиграл`/`сделал фолд` in `*** ИТОГ ***`
- No showdown → returns `None`

---

## Stage 8: Effective stack + villain list computation

**Goal:** Compute effective stack in BB and determine villain positions for header.

**Deliverables:**
- `utils/stacks.py` — `compute_eff_stack_bb(hero_chips: float, villain_chips: list[float], bb: float) -> int`
- `utils/villains.py` — `compute_villains(actions: list[Action], hero_name: str, positions: dict) -> list[str]`
- `tests/test_stacks.py` — floor rounding, multiple villains, exact division
- `tests/test_villains.py` — fold-before-hero omitted, voluntary-put-chips required, hero immediate fold lists SB/BB

**Acceptance criteria:**
- `min(hero, min(villains)) / bb`, rounded down (floor)
- Villains who fold before Hero's first action excluded
- Villains who voluntarily put chips in pot while Hero active included
- Hero folds immediately → only SB/BB listed (if applicable)

---

## Stage 9: Bet size quantization

**Goal:** Convert raw bet amounts to fraction-of-pot or Xbb notation.

**Deliverables:**
- `utils/betsize.py` — `quantize_size(bet_amount: float, pot_before: float, bb: float, eff_stack_bb: int) -> str`
- `tests/test_betsize.py` — 1/3 pot (within ±5%), 1/2 pot, 2/3 pot, 3/4 pot, pot, no-match → Xbb, edge of ±5% window, all-in for eff stack (omit size), all-in for less (include size)

**Acceptance criteria:**
- Bet within ±5% of fraction → fraction label
- Bet outside all fractions → `Xbb` rounded to 1 decimal
- All-in matching eff stack → `a` (no size)
- All-in not matching → `a Xbb`

---

## Stage 10: Output formatter

**Goal:** Assemble a parsed `Hand` into the compact notation string.

**Deliverables:**
- `formatter.py` — `format_hand(hand: Hand, hand_number: int) -> str`
- `tests/test_formatter.py` — full hand with all streets, preflop-only fold, showdown hand, no-showdown win

**Acceptance criteria:**
- Output matches notation.md format exactly: `Hand#N`, header line, `PF:`, `F [cards]:`, `T [card]:`, `R [card]:`, `SD:`, `Result:`
- Actions separated by ` / `
- Blinds implicit (not recorded as actions)
- Hero fold stops notation at fold point
- Blank line between hands

---

## Stage 11: Full pipeline integration + CLI

**Goal:** Wire everything together; `python converter.py input.txt` produces correct output.

**Deliverables:**
- `converter.py` — main entry point: read file → split → parse → compute → format → print
- `tests/test_integration.py` — end-to-end tests using synthetic hand strings and the sample file

**Acceptance criteria:**
- `python converter.py doc/sample_input.txt` produces correct output for all 20 hands
- Hero-absent hands (hand #15, hand #17) skipped with no output, no counter increment
- Sequential numbering across table changes
- Hands where Hero folds preflop output `Result: fold`
- Exit code 0 on success, non-zero on file-not-found

---

## Stage 12: Edge cases and hardening

**Goal:** Cover remaining required test scenarios and corner cases.

**Deliverables:**
- Additional tests in `tests/` for:
  - Multi-hand sequential numbering across table changes
  - Hero absent hand (skip, counter not incremented)
  - All-in for less with partial call
  - Set vs trips distinction at showdown
  - BB walk (everyone folds to BB)
- Any parser fixes needed to pass these tests

**Acceptance criteria:**
- All 10 required test categories from AGENTS.md pass
- No `UNKNOWN` output on the sample file (all data is unambiguous)