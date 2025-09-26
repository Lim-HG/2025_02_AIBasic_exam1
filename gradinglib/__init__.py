from .grader import Grader
from .submit import save_result_to_sheet

def grade_exam(student_id, name, answers: dict, sheet_name: str, creds_json_path: str):
    """
    학생 답안을 채점하고 결과를 지정된 Google Sheet에 저장합니다.
    """
    grader = Grader()
    score, feedback = grader.grade(answers)
    
    # Google Sheets에 결과 저장
    result_message = save_result_to_sheet(
        student_id, name, score, feedback, sheet_name, creds_json_path
    )
    
    return score, feedback, result_message
