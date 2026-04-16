from dotenv import load_dotenv
import os
from google.cloud import speech

load_dotenv()
STT_KEY = os.getenv("GOOGLE_STT_API_KEY")


def google_stt_transcribe(audio_content: bytes) -> str:
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # wav
        sample_rate_hertz=16000,
        language_code="ko-KR",
        model="command_and_search",
        use_enhanced=True,
    )
    try:
        response = client.recognize(config=config, audio=audio)
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        return transcript.strip()

    except Exception as e:
        print(f"STT error: {e}")
        return ""


def determine_answer(text: str) -> int:
    """텍스트를 보고 1~4번 중 무엇인지 결정 (판정 불가 시 0)"""
    if not text:
        return 0

    if any(keyword in text for keyword in ["1", "없", "전혀"]):
        return 1
    elif any(keyword in text for keyword in ["2", "가끔", "조금"]):
        return 2
    elif any(keyword in text for keyword in ["3", "종종", "자주"]):
        return 3
    elif any(keyword in text for keyword in ["4", "거의", "대부분"]):
        return 4
    else:  # 판정 불가
        return 0


def preload_model():
    client = speech.SpeechClient()
