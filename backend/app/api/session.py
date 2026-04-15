from fastapi import APIRouter
from app.store import sessions, responses
from app.models.schema import UserRequest
from uuid import uuid4

router = APIRouter()


@router.post("")
def create_session(req: UserRequest):
    session_id = str(uuid4())

    sessions[session_id] = {"user_name": req.user_name, "current_q": 0}
    responses[session_id] = []

    return {"session_id": session_id}