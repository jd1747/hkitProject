from core.config import SCORE_THRESHOLD

# from app.store import responses


def get_score(data):
    total_score = sum(data)
    result = "주의 필요" if total_score >= SCORE_THRESHOLD else "정상 범위"
    return result, total_score


def calc_score(answers: list) -> int:
    total_score = sum(a["value"] for a in answers)
    return total_score
