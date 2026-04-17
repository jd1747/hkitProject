from tempfile import NamedTemporaryFile
import whisper
import os
import shutil

model = whisper.load_model("base")


def preload_model():
    return whisper.load_model("base")  # tiny, base, small, etc.


def transcribe_audio(audio_file, model) -> int:
    """음성 -> 텍스트 변환 & 선택지 판단"""
    temp_path = ""
    try:
        suffix = f".{audio_file.filename.split('.')[-1]}"
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(audio_file.file, temp_file)
            temp_path = temp_file.name

        result = model.transcribe(temp_path, language="ko", fp16=False)
        text = result["text"].strip()
        return decide_answer(text)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def decide_answer(text: str) -> int:
    """텍스트 내용에서 선택지 번호를 추출"""
    clean_text = text.replace(" ", "")

    # 선택지 판정 관련 코드 (임시)
    mapping = {
        "1번": 1,
        "일번": 1,
        "첫번째": 1,
        "2번": 2,
        "이번": 2,
        "두번째": 2,
        "3번": 3,
        "삼번": 3,
        "세번째": 3,
        "4번": 4,
        "사번": 4,
        "네번째": 4,
    }

    for key, value in mapping.items():
        if key in clean_text:
            return value

    return 0
