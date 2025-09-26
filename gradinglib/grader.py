import json
import os

class Grader:
    def __init__(self):
        # __file__은 현재 파일의 경로를 나타냅니다.
        # 이 경로를 기준으로 answers.json 파일의 위치를 찾습니다.
        path = os.path.join(os.path.dirname(__file__), "answers.json")
        with open(path, "r", encoding="utf-8") as f:
            self.answers = json.load(f)

    def grade(self, student_answers: dict):
        score = 0
        feedback = []
        for qid, correct in self.answers.items():
            # 학생 답안이 set인 경우 list로 변환하여 비교
            correct_answer = correct
            student_answer = student_answers.get(qid, None)
            
            # 정답과 학생 답안의 타입을 유연하게 비교하기 위한 처리
            if isinstance(correct_answer, list) and isinstance(student_answer, set):
                student_answer = sorted(list(student_answer))
                correct_answer = sorted(correct_answer)

            if student_answer == correct_answer:
                score += 1
                feedback.append(f"{qid}: 정답 ✅")
            else:
                feedback.append(f"{qid}: 오답 ❌ (정답: {correct})")
        return score, "\n".join(feedback)