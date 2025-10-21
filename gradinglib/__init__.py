from .grader import Grader
from .submit import (
    save_result_via_appsscript,
    make_signature,
    build_submit_url,
    show_submit_button,
)

def grade_exam(student_id, name, answers: dict, app_script_url: str,
               assignment: str = "MLDL-2", email: str = "", api_key: str = ""):
    grader = Grader()
    score, feedback = grader.grade(answers)
    result_message = save_result_via_appsscript(
        student_id=student_id, name=name,
        score=score, feedback=feedback,
        app_script_url=app_script_url,
        assignment=assignment, email=email,
        api_key=api_key
    )
    return score, feedback, result_message


def grade_and_render_submit(
    *,
    student_id: str,
    name: str,
    exam_code: str,
    answers: dict,
    webapp_url: str,
    secret: str | bytes,
    title: str = "채점 완료",
):
    """
    [추천] 채점 후 제출 버튼을 표시합니다.
    (Apps Script 1회 제출 흐름용)
    """
    grader = Grader()
    score, feedback = grader.grade(answers)
    url = show_submit_button(
        webapp_url, secret,
        student_id=student_id, name=name,
        exam_code=exam_code, score=score, feedback=feedback, title=title
    )
    return score, feedback, url
