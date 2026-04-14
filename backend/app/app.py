from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
import csv
# import os
from datetime import datetime
from pathlib import Path
import json

from models.schema import UserRequest, AnswerRequest

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
with open(Path("backend/app/api/data/questions.json"), "rb", encoding="utf-8-sig") as f:
    questions = json.load(f)


# -------------------------
# CSV 헤더 생성
# -------------------------
DATA_DIR = Path("backend/app/data")
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
# 2. 질문 조회 (questions type 변경된 점 반영 필요함)
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

    with open(Path(DATA_DIR / "response.csv"), "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    # 결과 계산
    total_score = sum(data)
    result = "주의 필요" if total_score >= 19 else "정상 범위"

    # ======================
    # results.csv 저장
    # ======================
    row2 = [session_id, user_name, timestamp, total_score, result]

    with open(Path(DATA_DIR / "results.csv"), "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(row2)

    return {"message": "저장 완료"}
