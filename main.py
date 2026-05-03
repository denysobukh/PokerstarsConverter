import re
import argparse
from dataclasses import dataclass, field
from typing import Optional


# --- Data Structures ---

@dataclass
class HandMeta:
    hand_id: str
    stakes: str
    sb: float
    bb: float
    datetime: str
    table_name: str
    max_players: int
    button_seat: int


@dataclass
class SeatInfo:
    seat_number: int
    name: str
    stack_chips: float


@dataclass
class Action:
    position: str
    action_code: str
    amount_usd: Optional[float] = None
    size_str: str = ""


@dataclass
class StreetSegment:
    street: str
    board_cards: list
    lines: list


@dataclass
class ShowdownEntry:
    player: str
    position: str
    cards: str
    hand_name: str


@dataclass
class HandData:
    meta: HandMeta
    seats: dict
    hero_name: str
    hero_seat: int
    positions: dict
    hero_position: str
    streets: list
    hero_cards: str
    showdown: list
    result: str
    eff_stack_bb: int
    actions: dict = field(default_factory=dict)


# --- Stage 1: File Ingestion & Hand Splitting ---

def split_hands(text: str) -> list:
    parts = re.split(r'\*{11}\s+№\d+\s+\*{14}', text)
    hands = []
    for part in parts:
        stripped = part.strip()
        if stripped and not stripped.startswith('Выписка'):
            hands.append(stripped)
    return hands


# --- Stage 2: Header Parser ---

def parse_header(hand_text: str) -> HandMeta:
    lines = hand_text.split('\n')
    first_line = lines[0]

    m_id = re.search(r'Раздача PokerStars №(\d+)', first_line)
    hand_id = m_id.group(1) if m_id else ''

    m_stakes = re.search(r'\(\$([0-9.]+)/\$([0-9.]+)\s+[^)]*\)', first_line)
    sb = float(m_stakes.group(1)) if m_stakes else 0.0
    bb = float(m_stakes.group(2)) if m_stakes else 0.0
    stakes = f"${sb}/${bb}" if m_stakes else ''

    m_dt = re.search(r'(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})', first_line)
    datetime_str = m_dt.group(1) if m_dt else ''

    table_line = lines[1] if len(lines) > 1 else ''
    m_table = re.search(r"Стол '([^']+)'", table_line)
    table_name = m_table.group(1) if m_table else ''

    m_max = re.search(r'(\d+)-max', table_line)
    max_players = int(m_max.group(1)) if m_max else 6

    m_btn = re.search(r'Баттон на месте №(\d+)', table_line)
    button_seat = int(m_btn.group(1)) if m_btn else 0

    return HandMeta(
        hand_id=hand_id, stakes=stakes, sb=sb, bb=bb,
        datetime=datetime_str, table_name=table_name,
        max_players=max_players, button_seat=button_seat
    )


# --- Stage 3: Seat & Stack Table ---

def parse_seats(hand_text: str) -> tuple:
    seats = {}
    hero_name = ''
    for line in hand_text.split('\n'):
        m_seat = re.match(r'Место (\d+):\s+(\S+)\s+\(\$([0-9.]+)\s+фишек\)', line)
        if m_seat:
            seat_num = int(m_seat.group(1))
            name = m_seat.group(2)
            stack = float(m_seat.group(3))
            seats[seat_num] = SeatInfo(seat_num, name, stack)

        m_hero = re.match(r'Карты\s+(\S+)\s+\[', line)
        if m_hero:
            hero_name = m_hero.group(1)

    return seats, hero_name


# --- Stage 4: Position Assignment ---

POSITION_LABELS = {
    6: ['UTG', 'MP', 'CO', 'BU', 'SB', 'BB'],
    5: ['UTG', 'CO', 'BU', 'SB', 'BB'],
    4: ['CO', 'BU', 'SB', 'BB'],
    3: ['BU', 'SB', 'BB'],
    2: ['BU', 'BB'],
}


def get_position_labels(num_players: int) -> list:
    if num_players >= 6:
        return POSITION_LABELS[6]
    return POSITION_LABELS.get(num_players, POSITION_LABELS[2])


def assign_positions(meta: HandMeta, seats: dict, hero_name: str, hand_text: str) -> tuple:
    sb_name = ''
    bb_name = ''
    for line in hand_text.split('\n'):
        m_sb = re.match(r'(\S+):\s+ставит малый блайнд', line)
        if m_sb:
            sb_name = m_sb.group(1)
        m_bb = re.match(r'(\S+):\s+ставит большой блайнд', line)
        if m_bb:
            bb_name = m_bb.group(1)

    seat_names = {s: seats[s].name for s in seats}
    name_to_seat = {name: seat for seat, name in seat_names.items()}

    active_seats = sorted(seats.keys())
    num_active = len(active_seats)
    labels = get_position_labels(num_active)

    btn_seat = meta.button_seat
    seat_index = {s: i for i, s in enumerate(active_seats)}

    positions = {}
    if btn_seat in seat_index:
        btn_idx = seat_index[btn_seat]
        for i, label in enumerate(labels):
            seat_idx = (btn_idx + 1 + i) % num_active
            for s in active_seats:
                if seat_index[s] == seat_idx:
                    positions[seats[s].name] = label
                    break
    else:
        for i, label in enumerate(labels):
            if i < len(active_seats):
                positions[seats[active_seats[i]]] = label

    hero_pos = positions.get(hero_name, '')
    return positions, hero_pos


# --- Stage 5: Street Segmentation ---

def segment_streets(hand_text: str) -> list:
    segments = []
    current_street = None
    current_cards = []
    current_lines = []

    street_markers = [
        ('*** ЗАКРЫТЫЕ КАРТЫ ***', 'PF'),
        ('*** ФЛОП ***', 'F'),
        ('*** ТЕРН ***', 'T'),
        ('*** РИВЕР ***', 'R'),
        ('*** ВСКРЫТИЕ КАРТ ***', 'SD'),
        ('*** ИТОГ ***', 'SUMMARY'),
    ]

    for line in hand_text.split('\n'):
        matched = False
        for marker, street_name in street_markers:
            if marker in line:
                if current_street is not None:
                    segments.append(StreetSegment(current_street, current_cards, current_lines))
                current_street = street_name
                current_cards = []
                current_lines = []

                if street_name in ('F', 'T', 'R'):
                    all_brackets = re.findall(r'\[([^\]]+)\]', line)
                    if street_name == 'F' and all_brackets:
                        current_cards = all_brackets[0].strip().split()
                    elif street_name in ('T', 'R') and len(all_brackets) >= 2:
                        current_cards = all_brackets[1].strip().split()
                matched = True
                break

        if not matched and current_street is not None and current_street != 'SUMMARY':
            stripped = line.strip()
            if (stripped
                    and not stripped.startswith('Неуравненная')
                    and 'получил' not in stripped
                    and 'не показывает' not in stripped
                    and 'покидает' not in stripped
                    and 'садится' not in stripped
                    and 'истекло' not in stripped):
                current_lines.append(stripped)

    return segments


# --- Stage 6: Action Parser ---

def parse_action_line(line: str, positions: dict) -> Optional[Action]:
    m_player = re.match(r'(\S+):\s+(.+)', line)
    if not m_player:
        return None

    player_name = m_player.group(1)
    action_text = m_player.group(2).strip()
    position = positions.get(player_name, player_name)

    if 'фолд' in action_text:
        return Action(position, 'f')
    elif 'чек' in action_text:
        return Action(position, 'x')
    elif 'олл-ин' in action_text and ('колл' in action_text or 'бет' in action_text or 'рейз' in action_text):
        return Action(position, 'a')
    elif 'колл' in action_text:
        m_amt = re.search(r'\$([0-9.]+)', action_text)
        amount = float(m_amt.group(1)) if m_amt else None
        return Action(position, 'c', amount)
    elif 'бет' in action_text:
        m_amt = re.search(r'\$([0-9.]+)', action_text)
        amount = float(m_amt.group(1)) if m_amt else None
        return Action(position, 'b', amount)
    elif 'рейз' in action_text:
        m_amts = re.findall(r'\$([0-9.]+)', action_text)
        total = float(m_amts[-1]) if m_amts else None
        return Action(position, 'r', total)

    return None


def parse_actions(segment: StreetSegment, positions: dict) -> list:
    actions = []
    for line in segment.lines:
        action = parse_action_line(line, positions)
        if action:
            actions.append(action)
    return actions


# --- Stage 7: Sizing Formatter ---

def format_size(amount: Optional[float], pot: float, bb: float, street: str) -> str:
    if amount is None or bb <= 0:
        return ''

    if street == 'PF':
        bb_mult = round(amount / bb)
        return f"{bb_mult}bb"
    else:
        if pot <= 0:
            return f"{round(amount / bb)}bb"
        ratio = amount / pot
        if ratio <= 0.38:
            return "1/3"
        elif ratio <= 0.58:
            return "1/2"
        elif ratio <= 0.72:
            return "2/3"
        else:
            return "pot"


def apply_sizing(actions: list, segment: StreetSegment, bb: float, pot_tracker: dict) -> list:
    pot = pot_tracker.get('pot', 0)
    previous_bet = pot_tracker.get('previous_bet', 0)

    for action in actions:
        if action.action_code == 'f':
            pass
        elif action.action_code == 'x':
            pass
        elif action.action_code == 'c':
            pot += (action.amount_usd or 0)
            previous_bet = 0
        elif action.action_code == 'b':
            size = format_size(action.amount_usd, pot, bb, segment.street)
            action.size_str = size
            pot += (action.amount_usd or 0)
            previous_bet = action.amount_usd or 0
        elif action.action_code == 'r':
            size = format_size(action.amount_usd, pot, bb, segment.street)
            action.size_str = size
            increment = (action.amount_usd or 0) - previous_bet
            pot += max(increment, 0)
            previous_bet = action.amount_usd or 0
        elif action.action_code == 'a':
            pass

    pot_tracker['pot'] = pot
    pot_tracker['previous_bet'] = previous_bet
    return actions


# --- Stage 8: Hero Card Parser ---

def parse_hero_cards(hand_text: str) -> str:
    m = re.search(r'Карты\s+\S+\s+\[([^\]]+)\]', hand_text)
    if m:
        cards_str = m.group(1).strip()
        cards = cards_str.split()
        return ''.join(cards)
    return ''


# --- Stage 9: Showdown Parser ---

HAND_TRANSLATIONS = [
    ('стрит-флеш', 'straight flush'),
    ('стрит', 'straight'),
    ('флеш', 'flush'),
    ('фулл-хаус', 'full house'),
    ('каре', 'quads'),
    ('пару', 'pair'),
    ('две пары', 'two pair'),
    ('сет', 'set'),
    ('тройка', 'trips'),
    ('старшую карту', 'high card'),
    ('старшая карта', 'high card'),
]


def translate_hand(russian: str) -> str:
    ru_lower = russian.lower()
    for ru, en in HAND_TRANSLATIONS:
        if ru in ru_lower:
            return en
    return 'unknown'


def parse_showdown(hand_text: str, positions: dict, hero_name: str) -> list:
    entries = []
    for line in hand_text.split('\n'):
        m = re.match(r'(\S+):\s+открывает\s+\[([^\]]+)\]\s+\((.+)\)', line)
        if m:
            player = m.group(1)
            cards = m.group(2).strip()
            desc = m.group(3).strip()
            if player != hero_name:
                pos = positions.get(player, player)
                hand_name = translate_hand(desc)
                entries.append(ShowdownEntry(player, pos, cards, hand_name))
    return entries


# --- Stage 10: Result Parser ---

def parse_result(hand_text: str, hero_name: str, has_showdown: bool) -> str:
    itog_start = hand_text.find('*** ИТОГ ***')
    if itog_start == -1:
        return 'unknown'

    itog_section = hand_text[itog_start:]
    hero_lines = [l for l in itog_section.split('\n') if hero_name in l]

    for line in hero_lines:
        if 'выиграл' in line or 'собрал' in line:
            if not has_showdown:
                return 'won no SD'
            return 'won'
        if 'проиграл' in line:
            return 'lost'

    return 'unknown'


# --- Stage 11: Effective Stack Calculator ---

def calc_eff_stack(seats: dict, hero_name: str, bb: float) -> int:
    hero_stack = None
    for s in seats.values():
        if s.name == hero_name:
            hero_stack = s.stack_chips
            break

    if hero_stack is None or bb <= 0:
        return 0

    min_villain_stack = float('inf')
    for s in seats.values():
        if s.name != hero_name:
            min_villain_stack = min(min_villain_stack, s.stack_chips)

    eff = min(hero_stack, min_villain_stack) if min_villain_stack != float('inf') else hero_stack
    return round(eff / bb)


# --- Stage 12: Short Notation Assembler ---

def assemble(hand_data: HandData) -> str:
    lines = []

    villain_positions = []
    seen_villains = set()
    for street_name in ['PF', 'F', 'T', 'R']:
        if street_name in hand_data.actions:
            for action in hand_data.actions[street_name]:
                if (action.position != hand_data.hero_position
                        and action.position not in seen_villains):
                    villain_positions.append(action.position)
                    seen_villains.add(action.position)

    if not villain_positions:
        villain_positions = ['?']

    header = f"{hand_data.hero_cards} {hand_data.hero_position} {hand_data.eff_stack_bb}bb vs {','.join(villain_positions)}"
    lines.append(header)

    street_order = ['PF', 'F', 'T', 'R']
    for street in street_order:
        if street in hand_data.actions:
            actions = hand_data.actions[street]
            board = ''
            if street in ('F', 'T', 'R'):
                for seg in hand_data.streets:
                    if seg.street == street and seg.board_cards:
                        board = ' '.join(seg.board_cards)
                        break

            action_strs = []
            for a in actions:
                if a.size_str:
                    action_strs.append(f"{a.position} {a.action_code} {a.size_str}")
                else:
                    action_strs.append(f"{a.position} {a.action_code}")

            if board:
                lines.append(f"{street} [{board}]: {' / '.join(action_strs)}")
            else:
                lines.append(f"{street}: {' / '.join(action_strs)}")

    for sd in hand_data.showdown:
        cards_str = sd.cards.replace(' ', '')
        lines.append(f"SD: {sd.position} {cards_str} = {sd.hand_name}")

    lines.append(f"Result: {hand_data.result}")

    return '\n'.join(lines)


# --- Stage 13: Main Pipeline ---

def process_hand(hand_text: str) -> Optional[str]:
    meta = parse_header(hand_text)
    seats, hero_name = parse_seats(hand_text)
    positions, hero_pos = assign_positions(meta, seats, hero_name, hand_text)
    streets = segment_streets(hand_text)
    hero_cards = parse_hero_cards(hand_text)

    pot_tracker = {'pot': meta.sb + meta.bb, 'previous_bet': 0}
    actions_by_street = {}
    for seg in streets:
        if seg.street == 'SUMMARY':
            continue
        raw_actions = parse_actions(seg, positions)
        sized_actions = apply_sizing(raw_actions, seg, meta.bb, pot_tracker)
        actions_by_street[seg.street] = sized_actions

    has_showdown = any(seg.street == 'SD' for seg in streets)
    result = parse_result(hand_text, hero_name, has_showdown)
    showdown = parse_showdown(hand_text, positions, hero_name)
    eff_bb = calc_eff_stack(seats, hero_name, meta.bb)

    hand_data = HandData(
        meta=meta, seats=seats, hero_name=hero_name,
        hero_seat=0, positions=positions, hero_position=hero_pos,
        streets=streets, hero_cards=hero_cards, showdown=showdown,
        result=result, eff_stack_bb=eff_bb, actions=actions_by_street
    )

    return assemble(hand_data)


def process_file(input_path: str, output_path: Optional[str] = None) -> None:
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    hands = split_hands(text)
    results = []
    for hand in hands:
        try:
            output = process_hand(hand)
            if output:
                results.append(output)
        except Exception as e:
            print(f"Error processing hand: {e}", flush=True)

    full_output = '\n\n'.join(results)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_output + '\n')
    else:
        print(full_output)


def main():
    parser = argparse.ArgumentParser(description='PokerStars hand history converter')
    parser.add_argument('input', help='Input .txt file with hand histories')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)', default=None)
    args = parser.parse_args()
    process_file(args.input, args.output)


if __name__ == '__main__':
    main()
