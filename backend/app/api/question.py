from fastapi import APIRouter
from app.store import sessions, questions

router = APIRouter()


@router.get("/{session_id}")
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