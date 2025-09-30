# gradinglib/grader.py

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

            # 1. 답안이 제출되지 않았거나 코드 오류로 None인 경우
            if student_answer is None:
                feedback.append(f"{qid}: 오답 ❌ (답안 미제출 또는 코드 오류)")
                continue

            # 2. 비교 전, 학생 답안의 타입을 정답과 유사하게 변환
            if isinstance(student_answer, (np.ndarray, pd.Series)):
                student_answer = student_answer.tolist()
            if isinstance(student_answer, tuple):
                student_answer = list(student_answer)
            if isinstance(student_answer, list) and student_answer and isinstance(student_answer[0], tuple):
                student_answer = [list(item) for item in student_answer]

            # 3. [핵심 수정] try-except 구문으로 모든 비교 오류를 처리
            try:
                # 정답과 학생 답안을 비교
                if student_answer == correct:
                    score += 1
                    feedback.append(f"{qid}: 정답 ✅")
                else:
                    # 값이 다른 경우
                    feedback.append(f"{qid}: 오답 ❌")
            except Exception as e:
                # 비교 과정 자체에서 오류가 발생하는 경우 (예: ValueError, TypeError 등)
                # 이 블록이 실행되면 스크립트가 멈추지 않고 오답 처리됩니다.
                print(f"DEBUG: {qid} 채점 중 오류 발생 - {e}") # 선생님만 볼 수 있는 디버깅 메시지
                feedback.append(f"{qid}: 오답 ❌ (답안의 형식이 올바르지 않습니다.")

        return score, "\n".join(feedback)
