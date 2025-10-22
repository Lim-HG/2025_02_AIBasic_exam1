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
            
            # --- [수정된 비교 로직] ---
            
            is_correct = False
            try:
                # 1순위: 숫자/배열 비교 (부동소수점 허용)
                # np.allclose는 int, float, list, ndarray, nested list/array 등
                # 대부분의 숫자형 데이터를 (근사치로) 안전하게 비교합니다.
                # (Q2_05, Q2_06, Q2_09, Q2_11, Q2_12, Q2_13, Q2_14, Q2_15, Q2_16 등)
                is_correct = np.allclose(student_answer, correct)

            except (TypeError, ValueError):
                # 2순위: allclose가 실패한 경우 (예: 문자열, 객체 리스트 등)
                try:
                    # np.array_equal (정확한 비교)
                    is_correct = np.array_equal(student_answer, correct)
                except Exception:
                    # 3순위: 파이썬 기본 비교
                    is_correct = (student_answer == correct)
            
            except Exception:
                pass # allclose에서 다른 예외 발생 시 (비교 불가)
            
            # --- [수정 끝] ---
            
            if is_correct:
                score += 1; feedback.append(f"{qid}: 정답 ✅")
            else:
                feedback.append(f"{qid}: 오답 ❌")
        
        return score, "\n".join(feedback)
