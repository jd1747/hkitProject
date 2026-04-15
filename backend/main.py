from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
import csv
# import os
from datetime import datetime
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 프론트 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# 메모리 저장소
# -------------------------
sessions = {}
responses = {}

# -------------------------
# 질문 리스트
# -------------------------
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


# -------------------------
# CSV 헤더 생성
# -------------------------
DATA_DIR = Path("app/data")
CSV_CONFIGS = [
    {
        "file_path": DATA_DIR / "response.csv",
        "columns": ["session_id", "user_name", "timestamp"] + [f"q{i+1}" for i in range(len(questions))],
    },
    {
        "file_path": DATA_DIR / "results.csv",
        "columns": ["session_id", "user_name", "timestamp", "total_score", "result"],
    }
]

def init_csv(file_path: Path, columns: list):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(file_path, mode="x", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(columns)
    except FileExistsError:
        pass


for config in CSV_CONFIGS:
    if not config["file_path"].exists():
        init_csv(**config)


# -------------------------
# Request 모델
# -------------------------
class UserRequest(BaseModel):
    user_name: str


class AnswerRequest(BaseModel):
    session_id: str
    answer: int  # 0 ~ 3


# 루트 경로 생성
@app.get("/")
def root():
    return {"message": "ADHD 설문 API 서버 실행 중"}


# -------------------------
# 1. 세션 생성
# -------------------------
@app.post("/session")
def create_session(req: UserRequest):
    session_id = str(uuid4())

    sessions[session_id] = {"user_name": req.user_name, "current_q": 0}

    responses[session_id] = []

    return {"session_id": session_id}


# -------------------------
# 2. 질문 조회
# -------------------------
@app.get("/question/{session_id}")
def get_question(session_id: str):
    session = sessions.get(session_id)

    if not session:
        return {"error": "Invalid session"}

    idx = session["current_q"]

    if idx >= len(questions):
        return {"message": "설문 완료"}

    return {
        "question_id": idx + 1,
        "text": questions[idx],
        "progress": f"{idx+1}/{len(questions)}",
    }


# -------------------------
# 3. 응답 저장
# -------------------------
@app.post("/answer")
def save_answer(req: AnswerRequest):
    session = sessions.get(req.session_id)

    if not session:
        return {"error": "Invalid session"}

    if req.answer not in [0, 1, 2, 3]:
        return {"error": "Invalid answer"}

    if session["current_q"] >= len(questions):
        return {"error": "Already finished"}

    responses[req.session_id].append(req.answer)
    session["current_q"] += 1

    return {"message": "저장 완료"}


# -------------------------
# 4. 결과 계산
# -------------------------
@app.get("/result/{session_id}")
def get_result(session_id: str):
    data = responses.get(session_id)

    if not data:
        return {"error": "No data"}

    total_score = sum(data)
    result = "주의 필요" if total_score >= 19 else "정상 범위"

    return {"total_score": total_score, "result": result}


# -------------------------
# 5. CSV 저장
# -------------------------
@app.post("/save/{session_id}")
def save_to_csv(session_id: str):
    if session_id not in sessions:
        return {"error": "Invalid session"}

    user_name = sessions[session_id]["user_name"]
    data = responses[session_id]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not data or len(data) < len(questions):
        return {"error": "Incomplete data"}

    # ======================
    # response.csv 저장
    # ======================
    row = [session_id, user_name, timestamp] + data

    with open("response.csv", "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    # 결과 계산
    total_score = sum(data)
    result = "주의 필요" if total_score >= 19 else "정상 범위"

    # ======================
    # results.csv 저장
    # ======================
    row2 = [session_id, user_name, timestamp, total_score, result]

    with open("results.csv", "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(row2)

    return {"message": "저장 완료"}
