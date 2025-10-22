# gradinglib/grader.py
import json, os, numpy as np, pandas as pd, inspect
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

SECRET_KEY = b'ThisIsASecretKeyForGrader256Bits'
ENCRYPTED_ANSWERS_FILE = "answers.enc"

def decrypt_data(key, file_path):
    with open(file_path, 'rb') as f:
        nonce = f.read(16); tag = f.read(16); ciphertext = f.read()
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    data = unpad(cipher.decrypt_and_verify(ciphertext, tag), AES.block_size).decode('utf-8')
    return json.loads(data)

class Grader:
    def __init__(self):
        # ... 기존 복호화 로직 동일
        try:
            module_path = os.path.dirname(inspect.getfile(self.__class__))
            enc_path = os.path.join(module_path, ENCRYPTED_ANSWERS_FILE)
            self.answers = decrypt_data(SECRET_KEY, enc_path) or {}
        except Exception:
            self.answers = {}
        # ✅ 총 문항 수(스케일링에 사용)
        self.total_questions = len(self.answers) if isinstance(self.answers, dict) else 0


    def _load_correct_answer(self, qid, correct_data):
        if isinstance(correct_data, str) and correct_data.startswith("FILE:"):
            file_name = correct_data[5:]
            path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), file_name)
            if file_name.endswith('.npy'):
                return np.load(path, allow_pickle=True)
        return correct_data

    def grade(self, student_answers: dict):
        score = 0
        feedback = []
        for qid, student_answer in student_answers.items():
            correct = self.answers.get(qid)
            correct = self._load_correct_answer(qid, correct)
            if correct is None:
                feedback.append(f"{qid}: 오답 ❌ (정답 없음)")
                continue
            
            # 비교 로직: list/np.ndarray/float 등 유형별 비교
            is_correct = False
            try:
                if isinstance(correct, np.ndarray):
                    student_array = np.array(student_answer)
                    is_correct = student_array.shape == correct.shape and np.allclose(student_array, correct)
                
                # [수정됨] 튜플/리스트 비교 로직
                elif isinstance(correct, list):
                    # 1. 리스트에 float이 포함된 경우 (예: [0.1, 0.2])
                    if any(isinstance(x,float) for x in correct):
                        is_correct = np.allclose(student_answer, correct)
                    # 2. 학생 답이 튜플이고 정답이 리스트인 경우 (예: Q2_01)
                    elif isinstance(student_answer, tuple):
                        is_correct = (list(student_answer) == correct)
                    # 3. 그 외 (리스트 vs 리스트)
                    else:
                        is_correct = (student_answer == correct)
                
                # 그 외 (int, str 등)
                else:
                    is_correct = (student_answer == correct)
            
            except Exception:
                pass # 비교 중 오류 발생 시 is_correct = False 유지
            
            if is_correct:
                score += 1; feedback.append(f"{qid}: 정답 ✅")
            else:
                feedback.append(f"{qid}: 오답 ❌")
        
        return score, "\n".join(feedback)
