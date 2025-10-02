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

        for qid, student_answer in student_answers.items():
            correct = self.answers.get(qid)

            if correct is None:
                feedback.append(f"{qid}: 오답 ❌ (채점 기준을 찾을 수 없습니다.)")
                continue

            if student_answer is None:
                feedback.append(f"{qid}: 오답 ❌")
                continue

            # 1. 학생 답안의 기본 타입을 list로 통일 (numpy, tuple 등)
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

            # 2. --- 핵심 변경 사항 ---
            # 정답이 상수(숫자, 문자열 등)일 때, 학생 답안이 [정답]이나 [[정답]]처럼
            # 리스트/튜플로 감싸져 있으면 값을 추출합니다.
            try:
                # correct가 리스트/튜플이 아닌 단일 값일 때만 이 로직을 실행
                if not isinstance(correct, (list, tuple)):
                    # 학생 답안이 1개짜리 리스트/튜플이면 계속해서 껍질을 벗겨냄
                    while isinstance(student_answer, (list, tuple)) and len(student_answer) == 1:
                        student_answer = student_answer[0]
            except Exception:
                # 이 과정에서 오류 발생 시 원래대로 진행
                pass


            # 3. 최종적으로 정답과 비교
            try:
                is_correct = False
                
                # 소수점 리스트 비교 (부동소수점 오차 처리)
                is_float_list = (
                    isinstance(student_answer, list) and isinstance(correct, list) and
                    student_answer and correct and
                    # 리스트의 첫 항목이 float인지 확인하여 소수점 리스트 여부 판단
                    all(isinstance(item, (float, int)) for item in student_answer) and
                    all(isinstance(item, (float, int)) for item in correct)
                )

                if is_float_list:
                    is_correct = np.allclose(student_answer, correct)
                else:
                    # 그 외 모든 경우 (정수, 문자열, 상수 등)
                    is_correct = (student_answer == correct)

                if is_correct:
                    score += 1
                    feedback.append(f"{qid}: 정답 ✅")
                else:
                    feedback.append(f"{qid}: 오답 ❌")
            except Exception:
                feedback.append(f"{qid}: 오답 ❌")

        return score, "\n".join(feedback)
