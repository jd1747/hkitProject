from fastapi import APIRouter
from app.store import responses
from app.services.result_service import get_score

router = APIRouter()


@router.get("/{session_id}")
def get_result(session_id: str):
    data = responses.get(session_id)

    if not data:
        return {"error": "No data"}

    total_score, result = get_score(data)
    return {"total_score": total_score, "result": result}
