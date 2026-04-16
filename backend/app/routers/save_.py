from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.store import sessions, responses, questions, CSV_CONFIGS, warn_score
import csv

router = APIRouter()


def append_to_csv(config_key: str, row: list):
    file_path = CSV_CONFIGS[config_key]["path"]
    with open(file_path, "a", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerow(row)


@router.post("/{session_id}")
def save_to_csv(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Invalid session")

    user_name = sessions[session_id]["user_name"]
    data = responses[session_id]

    if not data or len(data) < len(questions):
        return {"error": "Incomplete data"}

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # response.csv 저장
    append_to_csv("response", [session_id, user_name, timestamp] + data)

    # 결과 계산 + results.csv 저장
    total_score = sum(data)
    result = "주의 필요" if total_score >= warn_score else "정상 범위"

    append_to_csv("results", [session_id, user_name, timestamp, total_score, result])

    return {"message": "저장 완료", "result": result}
