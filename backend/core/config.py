from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

CSV_ENCODING = "utf-8-sig"
SCORE_THRESHOLD = 21