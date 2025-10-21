from .grader import Grader
from .submit import (
    save_result_via_appsscript,
    make_signature,
    build_submit_url,
    show_submit_button,
)

def grade_exam(student_id, name, answers: dict, app_script_url: str,
               assignment: str = "MLDL-2", email: str = "", api_key: str = ""):
    """
    (기존) 서버→서버 POST 제출 방식.
    요즘 정책(도메인 로그인 1회 + HMAC)에는 'grade_and_render_submit' 사용을 권장.
    """
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
    exam_code: str,        # exam1 / exam2 / exam3
    answers: dict,
    webapp_url: str,
    secret: str | bytes,
    title: str = "채점 완료",
) -> tuple[int, str, str]:
    """
    [권장] 채점만 수행하고, 코랩에서 '제출 페이지 열기' 버튼을 렌더링한다.
    반환: (score, feedback, url)
    """
    grader = Grader()
    score, feedback = grader.grade(answers)
    url = show_submit_button(
        webapp_url, secret,
        student_id=student_id, name=name, exam_code=exam_code,
        score=score, feedback=feedback, title=title
    )
    return score, feedback, url
