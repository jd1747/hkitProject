from uuid import uuid4
from app.store import sessions, responses

def initialize_user_session(user_name: str) -> str:
    session_id = str(uuid4())
    
    sessions[session_id] = {"user_name": user_name, "current_q": 0}
    responses[session_id] = []
    
    return session_id

def get_session_info(session_id: str):
    return sessions.get(session_id)