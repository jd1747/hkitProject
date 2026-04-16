from app.store import questions

question_numbers = len(questions)

def get_question_text(idx: int):
    if idx < question_numbers:
        return questions[idx]  # text