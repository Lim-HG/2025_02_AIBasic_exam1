import json
import os
import numpy as np
import pandas as pd 

class Grader:
    def __init__(self):
        path = os.path.join(os.path.dirname(__file__), "answers.json")
        with open(path, "r", encoding="utf-8") as f:
            self.answers = json.load(f)

    def grade(self, student_answers: dict):
        score = 0
        feedback = []
        for qid, correct in self.answers.items():
            student_answer = student_answers.get(qid)

            # --- 핵심 수정: NumPy/Pandas 타입을 리스트로 변환 ---
            # 학생 답안이 NumPy 배열이거나 Pandas Series이면 리스트로 변환합니다.
            if isinstance(student_answer, (np.ndarray, pd.Series)):
                student_answer = student_answer.tolist()
            # -------------------------------------------------

            # 튜플을 리스트로 변환하여 일관성 있게 비교합니다.
            if isinstance(student_answer, tuple):
                student_answer = list(student_answer)
            if student_answer and isinstance(student_answer[0], tuple):
                student_answer = [list(item) for item in student_answer]

            if student_answer == correct:
                score += 1
                feedback.append(f"{qid}: 정답 ✅")
            else:
                feedback.append(f"{qid}: 오답 ❌ (정답: {correct})")
        return score, "\n".join(feedback)
