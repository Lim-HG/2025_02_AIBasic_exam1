import json
import os
import numpy as np
import pandas as pd
import inspect
import sys
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ----------------------------------------------------
# ⚠️ 경고: 이 키는 encrypt_answers.py에서 사용한 키와 정확히 일치해야 합니다.
# ⚠️ 실제 환경에서는 키를 환경 변수에서 로드해야 합니다.
# ----------------------------------------------------
SECRET_KEY = b'ThisIsASecretKeyForGrader256Bits' # 32바이트로 수정된 키
ENCRYPTED_ANSWERS_FILE = "answers.enc"

def decrypt_data(key, file_path):
    """AES-256 GCM 모드로 암호화된 파일을 복호화하여 JSON 객체를 반환합니다."""
    try:
        with open(file_path, 'rb') as f:
            # Nonce(16) + Tag(16) + Ciphertext 순서대로 데이터 읽기
            nonce = f.read(16)
            tag = f.read(16)
            ciphertext = f.read()

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        
        # 복호화 및 인증 태그 검증 (검증 실패 시 ValueError 발생)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
        
        # Padding 제거 및 JSON 로드
        data = unpad(decrypted_data, AES.block_size).decode('utf-8')
        return json.loads(data)

    except ValueError:
        print("❌ Decryption Error: Key or file integrity check failed (Tag mismatch).")
        return None
    except Exception as e:
        print(f"❌ Decryption Error: Failed to read or process encrypted file: {e}")
        return None


class Grader:
    def __init__(self):
        try:
            # 1. 현재 모듈의 실제 경로를 가져옵니다.
            module_path = os.path.dirname(inspect.getfile(self.__class__))
            enc_path = os.path.join(module_path, ENCRYPTED_ANSWERS_FILE)
            
            # 2. 암호화된 파일을 복호화하여 answers 로드
            self.answers = decrypt_data(SECRET_KEY, enc_path)
            
            if self.answers is None:
                raise Exception("Decryption failed. Using empty answers.")

            self._base_dir = module_path
            # print(f"✅ Encrypted answers loaded and decrypted from: {enc_path}")

        except Exception as e:
            # 초기화 오류 발생 시, 복호화 오류일 가능성이 높습니다.
            print(f"❌ Initialization Error: Decryption or File Load Failed ({e})")
            self.answers = {}

    def _load_correct_answer(self, qid, correct_data):
        # ... (이후 _load_correct_answer 및 grade 메서드는 이전과 동일합니다.)
        if isinstance(correct_data, str) and correct_data.startswith("FILE:"):
            file_name = correct_data[5:]
            base_dir = getattr(self, '_base_dir', None)
            
            if not base_dir:
                try:
                    base_dir = os.path.dirname(inspect.getfile(self.__class__))
                except:
                    return None
            
            file_path = os.path.join(base_dir, file_name)
            
            try:
                if file_name.endswith('.npy'):
                    # print(f"Attempting to load NPY file: {file_path}")
                    return np.load(file_path, allow_pickle=True)
            except Exception as e:
                print(f"Error loading answer file for {qid}: [File Not Found] {file_path}")
                return None
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

            # 1. 학생 답안의 기본 타입을 list로 통일
            try:
                if isinstance(correct, np.ndarray) and isinstance(student_answer, (list, tuple)):
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
                    try:
                        student_array = np.array(student_answer)
                    except:
                        is_correct = False
                        feedback.append(f"{qid}: 오답 ❌ (답안 배열 변환 오류)")
                        continue

                    if student_array.shape != correct.shape:
                        is_correct = False
                    else:
                        is_correct = np.allclose(student_array, correct)
                        
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
```eof
