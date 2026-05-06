from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from pokerstars_converter.converter import main, parse_hand


if __name__ == "__main__":
    main()
