import sys
from parser.hand_splitter import split_hands


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <input_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: file not found -> {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    hands = split_hands(content)

    for i, hand in enumerate(hands, start=1):
        print(f"\n--- Hand {i} ---")
        print(hand)


if __name__ == "__main__":
    main()