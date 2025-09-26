from .grader import Grader
from .submit import save_result_via_appsscript

def grade_exam(student_id, name, answers: dict, app_script_url: str):
    """
    학생 답안을 채점하고 결과를 Apps Script를 통해 Google Sheet에 저장합니다.
    """
    grader = Grader()
    score, feedback = grader.grade(answers)
    
    # Apps Script로 결과 전송
    result_message = save_result_via_appsscript(
        student_id, name, score, feedback, app_script_url
    )
    
    return score, feedback, result_message
