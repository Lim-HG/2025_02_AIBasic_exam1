# gradinglib/grader.py (최종 버전)

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

            # 1. 답안 미제출 또는 코드 자체에 오류가 있는 경우
            if student_answer is None:
                feedback.append(f"{qid}: 오답 ❌")
                continue

            # 2. 비교 전, 학생 답안의 타입을 정답과 유사하게 변환
            #    이 과정에서 오류가 발생해도 안전하게 처리
            try:
                if isinstance(student_answer, (np.ndarray, pd.Series)):
                    student_answer = student_answer.tolist()
                if isinstance(student_answer, tuple):
                    student_answer = list(student_answer)
                if isinstance(student_answer, list) and student_answer and isinstance(student_answer[0], tuple):
                    student_answer = [list(item) for item in student_answer]
            except Exception:
                # 변환 과정 자체에서 오류가 나면 바로 오답 처리
                feedback.append(f"{qid}: 오답 ❌ (답안의 형식이 올바르지 않습니다.)")
                continue

            # 3. 최종적으로 정답과 비교
            try:
                if student_answer == correct:
                    score += 1
                    feedback.append(f"{qid}: 정답 ✅")
                else:
                    feedback.append(f"{qid}: 오답 ❌") # 정답 불일치
            except Exception:
                # 비교 연산(==) 자체가 불가능한 경우 (e.g., ValueError)
                feedback.append(f"{qid}: 오답 ❌")

        return score, "\n".join(feedback)
