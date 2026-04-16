from fastapi import APIRouter, HTTPException
from app.store import sessions, questions
from app.services import question_service

router = APIRouter()
total_count = question_service.question_numbers


@router.get("/{session_id}")
def get_question(session_id: str):
    session = sessions.get(session_id)

    if not session:
        raise HTTPException(status_code=500, detail="Invalid session")

    idx = session["current_q"]

    if idx < total_count:
        return {
            "question_id": idx + 1,
            "text": question_service.get_question_text(idx),
            "progress": f"{idx+1}/{total_count}",
        }
    else:
        return {"message": "설문 완료"}
