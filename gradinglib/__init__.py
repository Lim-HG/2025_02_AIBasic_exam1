# gradinglib/__init__.py
from .grader import Grader
from .submit import (
    save_result_via_appsscript,
    # make_signature, # (주석 처리된 상태 유지)
    # build_submit_url, # (주석 처리된 상태 유지)
    show_submit_button,
)

def grade_exam(student_id, name, answers: dict, app_script_url: str,
               assignment: str = "MLDL-2", email: str = "", api_key: str = ""):
    # (구 방식)
    grader = Grader()
    raw_score, feedback = grader.grade(answers)
    result_message = save_result_via_appsscript(
        student_id=student_id, name=name,
        score=raw_score,
        feedback=feedback,
        app_script_url=app_script_url,
        assignment=assignment, email=email,
        api_key=api_key
    )
    return raw_score, feedback, result_message


def grade_and_render_submit(
    *,
    student_id: str,
    name: str,
    exam_code: str,          
    answers: dict,
    webapp_url: str,
    secret: str | bytes,     
    title: str = "채점 완료",
    points_per_question: float | None = 10.0,
    scale_to_100: bool = False,               
    decimals: int = 0,                         
):
    """
    [수정됨] 
    채점은 하되, 상세 피드백을 서버로 전송하거나 Colab으로 반환하지 않습니다.
    """
    grader = Grader()
    # [1] 로컬에서 채점 및 상세 피드백 생성 (변수는 존재)
    raw_score, feedback = grader.grade(answers) 
    total = grader.total_questions or max(len(answers), 1)

    # [2] 최종 점수 계산
    if scale_to_100:
        final_score_float = round((raw_score / total) * 100.0, decimals)
    else:
        p = points_per_question if points_per_question is not None else 10.0
        final_score_float = round(raw_score * p, decimals)

    if decimals == 0:
        final_score = int(final_score_float)
    else:
        final_score = final_score_float

    # [3] [핵심 수정] 서버로 전송 및 HTML 버튼 생성
    debug_message = show_submit_button(
        webapp_url, secret,
        student_id=student_id, 
        name=name, 
        exam_code=exam_code,
        score=final_score, 
        feedback="", # 👈 상세 피드백 대신 빈 문자열을 전송
        title=title 
    )
    
    # [4] [핵심 수정] Colab 셀로 피드백 반환 차단
    return final_score, "상세 피드백은 제공되지 않습니다.", debug_message
