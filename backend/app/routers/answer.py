from fastapi import APIRouter, HTTPException
from app.models.answer import AnswerRequest
from app.store import sessions, questions, responses

router = APIRouter()


@router.post("/{session_id}")
def save_answer(req: AnswerRequest):
    session = sessions.get(req.session_id)

    if not session:
        raise HTTPException(status_code=500, detail="Invalid session")

    if req.answer not in [1, 2, 3, 4]:
        return {"error": "Invalid answer"}

    if session["current_q"] >= len(questions):
        return {"error": "Already finished"}

    responses[req.session_id].append(req.answer - 1)
    session["current_q"] += 1

    return {"message": "저장 완료"}
