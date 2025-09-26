import json
import os
import numpy as np
import pandas as pd

class Grader:
    def __init__(self):
        # answers.json 파일 로드
        path = os.path.join(os.path.dirname(__file__), "answers.json")
        with open(path, "r", encoding="utf-8") as f:
            self.answers = json.load(f)

    def grade(self, student_answers: dict):
        score = 0
        feedback = []
        for qid, correct in self.answers.items():
            student_answer = student_answers.get(qid)

            # 1. NumPy 배열 또는 Pandas Series를 파이썬 리스트로 변환
            if isinstance(student_answer, (np.ndarray, pd.Series)):
                student_answer = student_answer.tolist()

            # 2. 튜플을 리스트로 변환
            if isinstance(student_answer, tuple):
                student_answer = list(student_answer)

            # 3. 중첩된 튜플을 리스트로 변환 (핵심 수정!)
            #    먼저 리스트인지 확인하고, 비어있지 않은지 확인한 후, 첫 항목을 검사합니다.
            if isinstance(student_answer, list) and student_answer and isinstance(student_answer[0], tuple):
                student_answer = [list(item) for item in student_answer]

            # 4. 최종 비교
            if student_answer == correct:
                score += 1
                feedback.append(f"{qid}: 정답 ✅")
            else:
                feedback.append(f"{qid}: 오답 ❌ (정답: {correct})")
        return score, "\n".join(feedback)
