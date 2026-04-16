from fastapi import APIRouter
from app.store import responses
from core.config import SCORE_THRESHOLD

router = APIRouter()


@router.get("/{session_id}")
def get_result(session_id: str):
    data = responses.get(session_id)

    if not data:
        return {"error": "No data"}

    total_score = sum(data)
    result = "주의 필요" if total_score >= SCORE_THRESHOLD else "정상 범위"

    return {"total_score": total_score, "result": result}