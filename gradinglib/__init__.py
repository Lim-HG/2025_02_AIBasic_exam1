from .grader import Grader
from .submit import save_result

def grade_exam(student_id, name, answers: dict):
    grader = Grader()
    score, feedback = grader.grade(answers)
    filepath = save_result(student_id, name, score, feedback)
    return score, feedback, filepath