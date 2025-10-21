# gradinglib/__init__.py
from .grader import Grader
from .submit import (
    save_result_via_appsscript,
    make_signature,
    build_submit_url,
    show_submit_button,
)

def grade_exam(student_id, name, answers: dict, app_script_url: str,
               assignment: str = "MLDL-2", email: str = "", api_key: str = ""):
    # (구 방식: 서버→서버 POST. 유지만 함)
    grader = Grader()
    raw_score, feedback = grader.grade(answers)
    result_message = save_result_via_appsscript(
        student_id=student_id, name=name,
        score=raw_score,  # ← 구 방식은 예전대로(원하면 동일하게 스케일링 가능)
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
    exam_code: str,          # exam1 / exam2 / exam3
    answers: dict,
    webapp_url: str,
    secret: str | bytes,
    title: str = "채점 완료",
    # ✅ 최종점수 스케일링 옵션 (둘 중 하나 택1)
    points_per_question: float | None = 10.0,  # 예: 문항당 10점 → 100점 만점
    scale_to_100: bool = False,                # True면 (정답수/총문항)*100
    decimals: int = 0,                         # 반올림 자리수
):
    """
    채점 후 '최종점수'를 산출하여 버튼을 렌더합니다.
    - 점수는 시트의 '점수' 열에 그대로 저장될 값입니다.
    - 시험코드는 URL 파라미터로 전달되고, 서버에서 [examX] 태그를 피드백 앞에 붙입니다.
    """
    grader = Grader()
    raw_score, feedback = grader.grade(answers)    # raw_score = 맞힌 문항 수
    total = grader.total_questions or max(len(answers), 1)

    # ✅ 최종점수 산출
    if scale_to_100:
        final_score_float = round((raw_score / total) * 100.0, decimals)
    else:
        # 기본: 문항당 배점 방식
        p = points_per_question if points_per_question is not None else 10.0
        final_score_float = round(raw_score * p, decimals)

    # [수정됨] decimals=0이면 int로 변환 (JSON 서명 일치용)
    if decimals == 0:
        final_score = int(final_score_float)
    else:
        final_score = final_score_float

    # ✅ 최종점수를 서명/URL/버튼에 사용
    url = show_submit_button(
        webapp_url, secret,
        student_id=student_id, name=name, exam_code=exam_code,
        score=final_score, feedback=feedback, title=title # 👈 수정된 final_score 사용
    )
    return final_score, feedback, url
