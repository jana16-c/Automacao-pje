from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from pje_automation.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
