# gradinglib/grader.py (수정된 최종 버전)

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

        # --- 핵심 변경 사항 ---
        # 전체 정답 파일이 아닌, "학생이 제출한 답안"을 기준으로 채점을 진행합니다.
        # 이렇게 하면 과제1, 과제2가 제출되어도 해당 과제의 문제만 정확히 채점할 수 있습니다.
        for qid, student_answer in student_answers.items():
            correct = self.answers.get(qid) # answers.json에서 해당 문제(qid)의 정답을 가져옵니다.

            # 1. 정답지에 해당 문제가 없는 경우
            if correct is None:
                feedback.append(f"{qid}: 오답 ❌ (채점 기준을 찾을 수 없습니다.)")
                continue

            # 2. 답안 미제출 또는 코드 자체에 오류가 있는 경우
            if student_answer is None:
                feedback.append(f"{qid}: 오답 ❌")
                continue

            # 3. 비교 전, 학생 답안의 타입을 정답과 유사하게 변환
            try:
                if isinstance(student_answer, (np.ndarray, pd.Series)):
                    student_answer = student_answer.tolist()
                if isinstance(student_answer, tuple):
                    student_answer = list(student_answer)
                if isinstance(student_answer, list) and student_answer and isinstance(student_answer[0], tuple):
                    student_answer = [list(item) for item in student_answer]
            except Exception:
                feedback.append(f"{qid}: 오답 ❌ (답안의 형식이 올바르지 않습니다.)")
                continue

            # 4. 최종적으로 정답과 비교
            try:
                if student_answer == correct:
                    score += 1
                    feedback.append(f"{qid}: 정답 ✅")
                else:
                    feedback.append(f"{qid}: 오답 ❌") # 정답 불일치
            except Exception:
                feedback.append(f"{qid}: 오답 ❌")

        return score, "\n".join(feedback)
