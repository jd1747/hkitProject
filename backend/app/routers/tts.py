from fastapi import APIRouter

router = APIRouter()


@router.post("/{session_id}")
def read_text():
    pass
