from fastapi import APIRouter, HTTPException
from app.models.session import UserRequest
from app.services.session_service import initialize_user_session

router = APIRouter()


@router.post("")
def create_session(req: UserRequest):
    if not req.user_name.strip():
        raise HTTPException(status_code=400, detail="이름을 입력해주세요.")

    try:
        session_id = initialize_user_session(req.user_name)
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"{e} :: 세션 생성 중 오류가 발생했습니다."
        )
