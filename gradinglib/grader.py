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
        module_path = os.path.dirname(inspect.getfile(self.__class__))
        enc_path = os.path.join(module_path, ENCRYPTED_ANSWERS_FILE)
        try:
            self.answers = decrypt_data(SECRET_KEY, enc_path)
        except Exception:
            self.answers = {}

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
                elif isinstance(correct, list):
                    is_correct = np.allclose(student_answer, correct) if any(isinstance(x,float) for x in correct) else (student_answer == correct)
                else:
                    is_correct = (student_answer == correct)
            except Exception:
                pass
            if is_correct:
                score += 1; feedback.append(f"{qid}: 정답 ✅")
            else:
                feedback.append(f"{qid}: 오답 ❌")
        return score, "\n".join(feedback)
