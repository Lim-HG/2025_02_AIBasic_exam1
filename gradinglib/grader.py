#  gradinglib/grader.py
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
            
            # --- [수정된 비교 로직: allclose가 False여도 array_equal 시도] ---
            is_correct = False
            try:
                ac = None
                try:
                    # 1) 근사 비교 (가능하면 사용)
                    ac = np.allclose(student_answer, correct)
                except Exception:
                    ac = None  # ragged 등으로 예외가 나면 근사 비교 생략

                if ac is True:
                    is_correct = True
                else:
                    # 2) 동등 비교 (리스트/튜플/np스칼라 혼재, ragged 대비)
                    try:
                        sa = np.asarray(student_answer, dtype=object)
                        ca = np.asarray(correct, dtype=object)
                        is_correct = np.array_equal(sa, ca)
                    except Exception:
                        # 3) 최후: 파이썬 기본 비교
                        is_correct = (student_answer == correct)

            except Exception:
                # 비교 과정에서 어떤 예외가 나도 마지막으로 기본 비교 시도
                try:
                    is_correct = (student_answer == correct)
                except Exception:
                    is_correct = False
            # --- [수정 끝] ---
            
            if is_correct:
                score += 1; feedback.append(f"{qid}: 정답 ✅")
            else:
                feedback.append(f"{qid}: 오답 ❌")
        
        return score, "\n".join(feedback)
