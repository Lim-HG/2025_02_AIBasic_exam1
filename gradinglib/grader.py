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

    def _load_correct_answer(self, qid, correct_data):
        if isinstance(correct_data, str) and correct_data.startswith("FILE:"):
            file_name = correct_data[5:]  # "FILE:" 문자열 제거
            base_dir = os.path.dirname(os.path.join(os.path.dirname(__file__), "answers.json"))
            file_path = os.path.join(base_dir, file_name)
            
            try:
                # .npy 파일 로드
                if file_name.endswith('.npy'):
                    return np.load(file_path)
                # 필요하다면 다른 파일 형식(CSV 등)도 여기에 추가 가능
            except Exception as e:
                print(f"Error loading answer file for {qid}: {e}")
                return None  # 로드 실패 시 None 반환
        return correct_data
        
    def grade(self, student_answers: dict):
        score = 0
        feedback = []

        for qid, student_answer in student_answers.items():
            correct = self.answers.get(qid)
            correct = self._load_correct_answer(qid, correct)

            if correct is None:
                feedback.append(f"{qid}: 오답 ❌ (채점 기준을 찾을 수 없습니다.)")
                continue

            if student_answer is None:
                feedback.append(f"{qid}: 오답 ❌")
                continue

            # 1. 학생 답안의 기본 타입을 list로 통일 (numpy, tuple 등)
            #    이 부분이 conf_mat(numpy 배열)를 list로 바꿔주어 문제를 해결합니다.
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

            # 2. 정답이 상수일 때, 학생 답안이 [정답] 등으로 감싸져 있으면 값을 추출
            try:
                if not isinstance(correct, (list, tuple)):
                    while isinstance(student_answer, (list, tuple)) and len(student_answer) == 1:
                        student_answer = student_answer[0]
            except Exception:
                pass


            # 3. 최종적으로 정답과 비교
            try:
                is_correct = False
                
                if isinstance(correct, np.ndarray):
                    # 학생 답안이 리스트이거나 스칼라 값일 수 있으므로 np.array로 변환
                    try:
                        student_array = np.array(student_answer)
                    except:
                        is_correct = False
                        feedback.append(f"{qid}: 오답 ❌ (답안 배열 변환 오류)")
                        continue

                    # 배열 크기가 다르면 오답
                    if student_array.shape != correct.shape:
                        is_correct = False
                    else:
                        # 부동소수점 오차를 고려하여 비교 (가장 일반적인 형태)
                        is_correct = np.allclose(student_array, correct)
                        
                # 소수점 리스트 비교 (부동소수점 오차 처리)
                is_float_list = False
                # 정답이 리스트이고 비어있지 않은지 먼저 확인
                if isinstance(correct, list) and correct:
                    # 첫번째 아이템을 기준으로 타입 체크 (중첩 리스트 고려)
                    first_val = correct[0]
                    if isinstance(first_val, list) and first_val:
                        first_val = first_val[0]
                    
                    # 최종적으로 확인된 첫번째 값이 float이면 소수점 리스트로 판단
                    if isinstance(first_val, float):
                        is_float_list = True

                if is_float_list:
                    is_correct = np.allclose(student_answer, correct)
                else:
                    # conf_mat와 같은 정수 리스트는 여기서 비교됨
                    is_correct = (student_answer == correct)

                if is_correct:
                    score += 1
                    feedback.append(f"{qid}: 정답 ✅")
                else:
                    feedback.append(f"{qid}: 오답 ❌")
            except Exception:
                feedback.append(f"{qid}: 오답 ❌")

        return score, "\n".join(feedback)
