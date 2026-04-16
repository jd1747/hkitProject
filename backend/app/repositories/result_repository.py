import csv
from pathlib import Path

DATA_DIR = Path("./data")
CSV_CONFIGS = {
    "response": {
        "path": DATA_DIR / "response.csv",
        "columns": ["session_id", "user_name", "timestamp"]
        + [f"q{i+1}" for i in range(20)],
    },
    "results": {
        "path": DATA_DIR / "results.csv",
        "columns": ["session_id", "user_name", "timestamp", "total_score", "result"],
    },
}


def init_csv():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for config in CSV_CONFIGS.values():
        file_path = config["path"]
        if not file_path.exists():
            with open(file_path, mode="x", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(config["columns"])
