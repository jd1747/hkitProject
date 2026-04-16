import csv
from pathlib import Path

questions = [
    "대화를 할 때 잘 듣지 않는 경우가 있다.",
    "지시를 잘 따르지 않거나 숙제, 임무 등을 완수하지 못하는 경우가 있다.",
    "과제나 업무를 수행하는 데 있어서 집중을 잘 못하고, 부주의로 인한 실수가 있다.",
    "지속적으로 정신력이 필요한 과제에 몰두하는 것을 피하거나, 거부하는 경우가 있다.",
    "수업이나 놀이에서 집중력을 유지하는 데 어려움을 겪는 경우가 있다.",
    "활동에 필요한 물건들을 종종 잃어버린다.(예: 준비물, 장난감, 숙제, 연필, 책 등)",
    "외부 자극에 의해 산만해진다.",
    "일상적인 일들을 종종 잊어버린다.",
    "대화 내용 또는 지시사항을 이해하거나 이행하기 등에 어려움을 느끼는 경우가 있다.",
    "손발이 가만히 있지 않으며, 자리에 앉아서는 계속 몸을 꿈틀거리는 일이 있다.",
    "조용히 앉아 있어야 하는 상황에 자리에서 일어나 다니는 경우가 종종 있다.",
    "상황에 맞지 않게 돌아다니거나 지나치게 산만해지는 경우가 있다.",
    "차분하게 노는 것, 놀이에 몰두하는 것에 어려움을 종종 느낀다.",
    "끊임없이 움직이거나, 꼼지락 거리는 행동을 하는 경우가 있다.",
    "지나치게 말을 많이 하는 경우가 있다.",
    "질문이 끝나기도 전에 불쑥 대답을 해버리는 경우가 있다.",
    "자기 차례를 기다리지 못하는 경우가 있다.",
    "다른 사람들의 대화나 활동 사이에 끼어들거나 참견하는 경우가 있다.",
    "차분히 앉아 있거나, 조용히 있는 상황을 견디는 것에 어려움을 겪는 경우가 있다.",
    "과제나 활동을 체계적으로 하는 데 종종 어려움을 겪는다.",
]

DATA_DIR = Path("./data")
CSV_CONFIGS = {
    "response": {
        "path": DATA_DIR / "response.csv",
        "columns": ["session_id", "user_name", "timestamp"]
        + [f"q{i+1}" for i in range(len(questions))],
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


sessions = {}
responses = {}

warn_score = 20
