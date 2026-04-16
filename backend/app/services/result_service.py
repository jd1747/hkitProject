from core.config import SCORE_THRESHOLD

# from app.store import responses


def get_result(data):
    total_score = sum(data)
    result = "주의 필요" if total_score >= SCORE_THRESHOLD else "정상 범위"
    return result, total_score
