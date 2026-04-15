from fastapi import APIRouter
from dotenv import load_dotenv
import os
from google.cloud.speech_v1 import SpeechClient
from google.cloud.speech_v1.types import cloud_speech
from app.store import sessions
from app.models.schema import UserRecord

load_dotenv()
STT_KEY = os.getenv("GOOGLE_STT_API_KEY")

router = APIRouter()


@router.get("/{session_id}")
def transcription(req: UserRecord):
    retry_count = req.retry_count
    # ...
    text = ""  # 인식 결과

    # 텍스트 기반으로 몇 번인지 판정 (모르겠으면 0)
    # ...
    
    answer = 1  # 선택지 판별 결과
    if answer == 0 and retry_count == 1:
        answer = -1
    
    return {"answer": answer}