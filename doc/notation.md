# Poker Hand Notation (fact-only)

---

## 1. Header

```
Hand#[HandIndex]
[HeroCards] [Position] [EffStackBB] vs [VillainPositions]
```

- **Hand#[HandIndex]**: sequential index of this hand within a session or recorded set. Always the first line. Starts at 1. Example: `Hand#1`, `Hand#11`, `Hand#42`.
- **HeroCards**: always include suits, except for pocket pairs which may omit suits.
- **EffStackBB**: effective stack in big blinds at the start of the hand.
- **VillainPositions**: lists all villains involved with Hero. Villains who are in the hand but not in a pot with Hero may be omitted.

Examples:
```
Hand#1
AdTd CO 80bb vs SB

Hand#2
AhKh BU 100bb vs BB

Hand#11
7s7c UTG 120bb vs MP, CO
```

---

## 2. Positions

### 2.1 Standard position labels

| Label | Full name | 6-max | 9-max | HU |
|-------|-----------|:-----:|:-----:|:--:|
| `UTG` | Under the Gun | ✓ | ✓ | — |
| `UTG+1` | Under the Gun +1 | — | ✓ | — |
| `UTG+2` | Under the Gun +2 | — | ✓ | — |
| `MP` | Middle Position | — | ✓ | — |
| `HJ` | Hijack | ✓ | ✓ | — |
| `CO` | Cutoff | ✓ | ✓ | — |
| `BU` | Button | ✓ | ✓ | ✓ |
| `SB` | Small Blind | ✓ | ✓ | — |
| `BB` | Big Blind | ✓ | ✓ | ✓ |

- `BU` is always used for the Button — never `BTN` or `D`.
- `HJ` is the standard label for the Hijack — never `MP2` or `MP3`.
- In heads-up (HU) play, only `BU` and `BB` are used. `BU` posts the small blind and acts first preflop.

### 2.2 Position order

Preflop action order (first to act → last to act):

```
UTG → UTG+1 → UTG+2 → MP → HJ → CO → BU → SB → BB
```

Postflop action order (first to act → last to act):

```
SB → BB → UTG → UTG+1 → ... → CO → BU
```

The Button (`BU`) always acts last postflop. The Small Blind (`SB`) always acts first postflop.

### 2.3 Positional concepts (for context only — not recorded in notation)

- **In position (IP)**: Hero acts after the villain on all postflop streets.
- **Out of position (OOP)**: Hero acts before the villain on all postflop streets.
- **Early position (EP)**: UTG, UTG+1, UTG+2.
- **Middle position (MP)**: MP, MP+1, HJ.
- **Late position (LP)**: CO, BU.
- **Blinds**: SB, BB — always OOP postflop (except vs each other).

These concepts are **never written into the notation**. Only position labels appear.

### 2.4 Examples

```
Hand#3
KsQs HJ 100bb vs CO, BU

Hand#7
AcAh SB 120bb vs BB

Hand#14
TsTc UTG 90bb vs MP, BU, BB
```

---

## 3. Streets

```
PF: ...
F [cards]: ...
T [card]: ...
R [card]: ...
SD: ...
```

- `PF` — preflop
- `F` — flop (3 board cards)
- `T` — turn (1 board card)
- `R` — river (1 board card)
- `SD` — showdown
- Board cards are always written in full suit format: `Ah3s8c`, `7s`, `Jd`
- Blinds (`SB`, `BB`) are **implicit** — they are not recorded as actions. `PF` action begins with the first player to act after the blinds (`UTG`, or the first live player in the hand).
- If Hero folds on any street, notation stops at Hero's fold action. Remaining villain action is not recorded. End the hand with `Result: fold`.

---

## 4. Actions (strict minimum — facts only)

```
f   fold
x   check
c   call   (preflop: call of any amount, including limping the BB)
b   bet    (first aggression on a street when no bet exists yet)
r   raise  (aggression over an existing bet or raise)
a   all-in
```

**No labels for intent or line type:**
- no "limp" — preflop call is written as `c`
- no "3bet", "4bet" — repeated raises are written as `r`
- no "check-raise" — written as `x` then `r` in sequence
- no "donk" — written as `b`

---

## 5. Action format

```
[position] [action] [size]
```

Actions within a street are separated by ` / `.

Example:
```
PF: CO r 2bb / SB r 8bb / CO c
F Ah3s8c: SB b 1/3 / CO c
T 7s: SB b 1/2 / CO c
R Jd: SB a / CO c
```

---

## 6. Bet sizes

Sizes for `b`, `r`, and `a` (when relevant):

```
Xbb     exact size in big blinds (e.g. 2bb, 2.5bb, 47bb)
1/3     one-third of pot
1/2     half pot
2/3     two-thirds of pot
3/4     three-quarters of pot
pot     pot-size bet
```

- Fractions refer to the pot **before** the bet is added (standard poker convention).
- `a` (all-in) is written without a size when the effective stack is already established in the header. When the all-in size is non-obvious or differs from effective stack (e.g. short all-in, partial raise), append the size: `a 47bb`.
- For any size not covered above, use exact `Xbb` notation.

---

## 7. Multiple players

List all active villain positions in the header. Record every action in order.

```
AdTd CO 80bb vs BU, SB

PF: UTG f / MP f / CO r 2.5bb / BU c / SB r 9bb / CO c / BU f
F Ah3s8c: SB b 1/3 / CO c
```

---

## 8. Showdown and result

**Showdown (cards seen):**
```
SD: [position] [cards] = [hand name]
Result: won / lost
```

**Result values:**
```
Result: won
Result: lost
Result: fold
```

- `Result: won` — Hero wins the pot (at showdown or without).
- `Result: lost` — Hero goes to showdown and loses.
- `Result: fold` — Hero folds at any street, including preflop.
- `Result` is always the last line and always present.
- `SD` line is only written when a showdown actually occurs. If Hero folds, omit `SD` entirely. If Hero wins without showdown, omit `SD` as well.

Examples:

**Hero loses at showdown:**
```
SD: SB Th9h = straight
Result: lost
```

**Hero wins at showdown:**
```
SD: SB KQo = pair
Result: won
```

**Hero wins, no showdown:**
```
Result: won
```

**Hero folds (any street):**
```
Result: fold
```

---

## 8a. Hand name enumeration

Use exactly these names — no variations, no abbreviations:

| # | Name | Example notation |
|---|------|-----------------|
| 1 | `high card` | `= high card` |
| 2 | `pair` | `= pair` |
| 3 | `two pair` | `= two pair` |
| 4 | `set` | `= set` *(pocket pair + matching board card)* |
| 5 | `trips` | `= trips` *(two board cards + one hole card match)* |
| 6 | `straight` | `= straight` |
| 7 | `flush` | `= flush` |
| 8 | `full house` | `= full house` |
| 9 | `quads` | `= quads` |
| 10 | `straight flush` | `= straight flush` |
| 11 | `royal flush` | `= royal flush` |

**Rules:**
- `set` and `trips` are distinguished because they represent different board textures and hand strengths. Use `set` when Hero/villain holds a pocket pair and one board card matches. Use `trips` when two board cards are paired and one hole card matches.
- Do not write `three of a kind` — use `set` or `trips` as appropriate.
- Do not add rank qualifiers in the SD line (e.g. do not write `= pair of aces` — just `= pair`).

---

## 9. Complete example (hand #11)

```
Hand#11
AdTd CO 80bb vs SB

PF: CO r 2bb / SB r 8bb / CO c
F Ah3s8c: SB b 1/3 / CO c
T 7s: SB b 1/2 / CO c
R Jd: SB a / CO c

SD: SB Th9h = straight
Result: lost
```

---

## 10. Quick reference

### Actions

| Symbol | Meaning |
|--------|---------|
| `f` | fold |
| `x` | check |
| `c` | call (incl. preflop limp) |
| `b` | bet (first aggression on street) |
| `r` | raise (over existing bet/raise) |
| `a` | all-in |
| `/` | next action in same street |

### Positions (9-max, preflop order)

| Label | Name |
|-------|------|
| `UTG` | Under the Gun |
| `UTG+1` | Under the Gun +1 |
| `UTG+2` | Under the Gun +2 |
| `MP` | Middle Position |
| `HJ` | Hijack |
| `CO` | Cutoff |
| `BU` | Button |
| `SB` | Small Blind |
| `BB` | Big Blind |

### Hand names (SD line)

| Rank | Name |
|------|------|
| 1 | `high card` |
| 2 | `pair` |
| 3 | `two pair` |
| 4 | `set` |
| 5 | `trips` |
| 6 | `straight` |
| 7 | `flush` |
| 8 | `full house` |
| 9 | `quads` |
| 10 | `straight flush` |
| 11 | `royal flush` |