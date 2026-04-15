from pydantic import BaseModel


class UserRequest(BaseModel):
    user_name: str


class AnswerRequest(BaseModel):
    session_id: str
    answer: int  # 0 ~ 3