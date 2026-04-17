from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from app.services.stt_service import transcribe_audio

router = APIRouter()


@router.post("/{session_id}")
def process_voice(
    request: Request, audio_file: UploadFile = File(...), retry_count: int = Form(...)
):

    model = request.app.state.model
    answer = transcribe_audio(audio_file, model)
    if answer == 0 and retry_count >= 1:
        answer = -1
    return {"answer": answer}
