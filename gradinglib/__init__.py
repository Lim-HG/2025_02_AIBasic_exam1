from .grader import Grader
from .submit import save_result_via_appsscript

def grade_exam(student_id, name, answers: dict, app_script_url: str, assignment: str = "MLDL-2", email: str = ""):
    grader = Grader()
    score, feedback = grader.grade(answers)

    result_message = save_result_via_appsscript(
        student_id=student_id, name=name,
        score=score, feedback=feedback,
        app_script_url=app_script_url,
        assignment=assignment, email=email
    )
    return score, feedback, result_message
