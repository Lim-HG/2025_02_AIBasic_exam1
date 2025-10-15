# gradinglib/grader.py (경로 문제 해결을 위한 수정)

import json
import os
import numpy as np
import pandas as pd
import sys
import inspect

class Grader:
    def __init__(self):
        # 모듈이 설치된 실제 디렉토리를 찾아 answers.json을 로드합니다.
        # inspect 모듈을 사용하여 현재 모듈의 파일 위치를 더 확실하게 가져옵니다.
        try:
            # 현재 파일의 실제 경로를 가져옵니다. (설치된 경우에도 작동)
            module_path = os.path.dirname(inspect.getfile(self.__class__))
            path = os.path.join(module_path, "answers.json")
            
            with open(path, "r", encoding="utf-8") as f:
                self.answers = json.load(f)
            self._base_dir = module_path # 정답 파일 로드를 위한 기본 경로 설정
            print(f"✅ answers.json loaded from: {path}")

        except Exception as e:
            # 파일 로드 실패 시 디버깅 정보 제공
            print(f"❌ Initialization Error (answers.json not found): {e}")
            self.answers = {} # 로드 실패 시 빈 딕셔너리로 초기화

    def _load_correct_answer(self, qid, correct_data):
        if isinstance(correct_data, str) and correct_data.startswith("FILE:"):
            file_name = correct_data[5:]  # "FILE:" 문자열 제거
            
            # __init__에서 설정한 패키지 설치 경로를 기본 경로로 사용
            base_dir = getattr(self, '_base_dir', os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_dir, file_name)
            
            try:
                # .npy 파일 로드
                if file_name.endswith('.npy'):
                    # 파일 로드 시도 전 경로 출력 (디버깅 목적)
                    print(f"Attempting to load NPY file: {file_path}")
                    return np.load(file_path, allow_pickle=True) # allow_pickle=True 추가
            except Exception as e:
                # 에러 발생 시 실패 경로를 명시
                print(f"Error loading answer file for {qid}: [File Not Found] {file_path}")
                return None  # 로드 실패 시 None 반환
        return correct_data
        
    # grade 함수 이하의 모든 채점 로직은 이전과 동일합니다.
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

            # 1. 학생 답안의 기본 타입을 list로 통일
            try:
                if isinstance(correct, np.ndarray) and isinstance(student_answer, (list, tuple)):
                    # 정답이 np.ndarray일 경우, 학생 답안을 변환하지 않고 바로 3단계에서 np.array로 변환하도록 건너뜁니다.
                    pass
                else:
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
                if not isinstance(correct, (list, tuple, np.ndarray)):
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
                elif isinstance(correct, list) and correct:
                    is_float_list = False
                    first_val = correct[0]
                    if isinstance(first_val, list) and first_val:
                        first_val = first_val[0]
                    
                    if isinstance(first_val, float):
                        is_float_list = True

                    if is_float_list:
                        is_correct = np.allclose(student_answer, correct)
                    else:
                        is_correct = (student_answer == correct)
                
                # 스칼라 값 비교
                else:
                    is_correct = (student_answer == correct)

                if is_correct:
                    score += 1
                    feedback.append(f"{qid}: 정답 ✅")
                else:
                    feedback.append(f"{qid}: 오답 ❌")
            except Exception:
                feedback.append(f"{qid}: 오답 ❌ (비교 중 예외 발생)")

        return score, "\n".join(feedback)
