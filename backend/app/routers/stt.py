from fastapi import APIRouter, File, UploadFile, Form, Depends
from app.services import stt_service

router = APIRouter()


class UserRecordRequest:
    def __init__(
        self,
        audio_file: UploadFile = File(...),
        retry_count: int = Form(...)
    ):
        self.audio_file = audio_file
        self.retry_count = retry_count


@router.post("/{session_id}")
async def process_voice(data: UserRecordRequest = Depends()):
    audio_content = await data.audio_file.read()
    transcript = stt_service.google_stt_transcribe(audio_content)
    retry_count = data.retry_count

    answer = stt_service.determine_answer(transcript)

    if answer == 0 and retry_count == 1:
        answer = -1

    return {"answer": answer}
