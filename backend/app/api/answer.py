from fastapi import APIRouter
from app.models.schema import AnswerRequest
from app.store import sessions, questions, responses

router = APIRouter()


@router.post("")
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