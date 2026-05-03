# Project Goal

Build a Python CLI tool that converts PokerStars hand-history logs (Russian or English locale) (Input sample: [sample_input.txt](doc/sample_input.txt))
into compact factual poker notation, as described in [notation.md](doc/notation.md).

The output must contain only facts — no strategic evaluation.

Usage:
    python converter.py <input_file.txt>

Output goes to stdout: one hand block per hand, separated by a single blank line.

---

# Input Format Notes

## Language
The sample file is a Russian-locale PokerStars export. All keyword matching must handle
Russian strings. Reference keyword table:

| Concept            | Russian keyword(s)                                 |
|--------------------|----------------------------------------------------|
| Hand separator     | `*********** №N **************`                   |
| Button seat        | `Баттон на месте №N`                               |
| Hole cards         | `Карты [PlayerName] [cards]`                       |
| Preflop            | `*** ЗАКРЫТЫЕ КАРТЫ ***`                           |
| Flop               | `*** ФЛОП ***`                                     |
| Turn               | `*** ТЕРН ***`                                     |
| River              | `*** РИВЕР ***`                                    |
| Showdown           | `*** ВСКРЫТИЕ КАРТ ***`                            |
| Summary            | `*** ИТОГ ***`                                     |
| Fold action        | `делает фолд`                                      |
| Call action        | `делает колл`                                      |
| Raise action       | `делает рейз $X $Y` (X = added, Y = total; use Y) |
| Bet action         | `делает бет`                                       |
| Check action       | `делает чек`                                       |
| All-in suffix      | `и олл-ин`                                         |
| Posts SB           | `ставит малый блайнд`                              |
| Posts BB           | `ставит большой блайнд`                            |
| Shows cards        | `открывает`                                        |

## Raise size format
`делает рейз $X $Y` — `$X` is the increment added, `$Y` is the total bet. Always use `$Y`
(the total) when computing the raise size in big blinds.

---

# Hero Identification

Hero is the player whose hole cards appear in the `Карты [name] [cards]` line
before any board cards are shown (i.e., in the preflop section). Extract the name from
this line and use it to identify Hero's seat, stack, and actions throughout the hand.

---

# Position Mapping

## Algorithm (6-max)
1. Collect all seated players in ascending seat-number order.
2. The button seat is given by `Баттон на месте №N`.
3. Starting from the button seat and going clockwise (ascending seat number, wrapping around),
   assign positions: BU → SB → BB → UTG → HJ → CO.
   - For fewer than 6 active players, remove positions from the early seats first
     (drop UTG before HJ, HJ before CO), keeping BU, SB, BB always present.
4. If a seat is listed in the roster but has no actions (busted/sitting-out), exclude them
   from the count before assigning positions.

## Labels
Always use `BU` for the button (never `BTN` or `D`). All labels per PokerNotationRules §2.1.

---

# Effective Stack

- Use `min(Hero_stack, villain_stack)` measured from chip counts **before** blinds are posted
  (the stack line at the top of the hand).
- When multiple villains are listed in the header, use `min(Hero_stack, min(villain_stacks))`.
- Round down to the nearest integer big blind (e.g. $1.51 / $0.02 = 75bb).

---

# Villain Definition (Header)

List all players who: (a) did not fold before Hero acted preflop, AND (b) voluntarily put
chips in the pot at some point while Hero was still active in the hand.
Players who fold before Hero's first action may be omitted.
If Hero folds preflop immediately (first to act), list only players who were in the BB/SB.

---

# Bet Size Quantization

Convert bet sizes to fractions when the actual size is within ±5% of the fraction of the
pot-before-bet. Standard fractions to test (in order): `1/3`, `1/2`, `2/3`, `3/4`, `pot`.
If no fraction matches within ±5%, use exact `Xbb` rounded to 1 decimal place (e.g. `2.5bb`).

All-in sizes: omit size when the all-in amount matches the effective stack stated in the
header (±0.5bb). Otherwise append the size (e.g. `a 47bb`). A call-all-in for less than
the facing bet is written `a Xbb` with explicit size.

---

# Special Preflop Cases

- **BB option check**: If the BB checks their option (after all others have called or folded),
  record it as `BB x` in the PF line.
- **Walk (everyone folds to BB)**: BB wins uncontested; Hero result is `Result: fold` if
  Hero folded, or `Result: won` if Hero is BB. No PF action line is needed if no voluntary
  action occurred.
- **Limp**: preflop call of the BB amount is written as `c` (no special label).

---

# Multi-Hand / Multi-Table Numbering

- Hands are numbered sequentially (`Hand#1`, `Hand#2`, …) in the order they appear in the
  input file, across all tables.
- If Hero is not present in a hand (not seated), skip that hand entirely (do not emit output
  and do not increment the counter).
- If Hero folds immediately preflop (first legal action), still output the hand with
  `Result: fold`.

---

# Output Format

## Full block format

```
Hand#N
[HeroCards] [HeroPosition] [EffStackBB] vs [VillainPositions]
PF: ...
F [cards]: ...
T [card]: ...
R [card]: ...
SD: [position] [cards] = [hand name]    ← only if showdown occurred
Result: won / lost / fold
```
---

# Implementation Rules

- Do not invent missing actions.
- Preserve exact hole cards and board cards (suit always explicit except pocket pairs).
- Use positions: UTG, HJ, CO, BU, SB, BB (and UTG+1, UTG+2, MP for 9-max).
- No evaluative language.
- If data is ambiguous, output `UNKNOWN`.
- Prefer simple parsing over clever inference.

---

# Testing

Use **pytest**. Write unit tests for every distinct parser behavior using small synthetic
hand-history strings (do not rely solely on the sample file). Required test coverage includes:

- Seat-to-position mapping for 2, 3, 4, 5, and 6 active players
- Raise size parsing (two-number format → total)
- Bet size quantization (fraction match, no-match, edge of ±5% window)
- Effective stack rounding
- Hero folds preflop (first action vs. after action)
- BB checks option
- All-in for less (partial call)
- Showdown: set vs. trips distinction
- Multi-hand sequential numbering across table changes
- Hand where Hero is absent (skipped, counter not incremented)
