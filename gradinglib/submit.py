# gradinglib/submit.py
import json
from typing import Any, Dict, Tuple
import requests


def _normalize_response(res: Dict[str, Any]) -> Tuple[str, str]:
    """
    서버(Apps Script) 응답을 단일 인터페이스로 정규화한다.
    반환: (status, reason)
      - status: "success" | "already_submitted" | "error"
      - reason: 부가 사유(없으면 빈 문자열)
    지원 스키마:
      A) { "ok": true/false, "reason"?: str, "message"?: str }
      B) { "status": "success"|"error", "reason"?: str, "message"?: str }
    """
    # 스키마 A 우선 처리
    if "ok" in res:
        if res.get("ok") is True:
            return "success", ""
        # ok=False일 경우
        reason = str(res.get("reason", "")).strip().lower()
        if reason == "already_submitted":
            return "already_submitted", reason or "already_submitted"
        return "error", reason

    # 스키마 B 처리
    if "status" in res:
        status = str(res.get("status", "")).strip().lower()
        reason = str(res.get("reason", "") or "").strip().lower()
        if status == "success":
            return "success", ""
        if reason == "already_submitted":
            return "already_submitted", reason
        if status == "error":
            return "error", reason

    # 알 수 없는 스키마
    return "error", ""


def save_result_via_appsscript(
    student_id: str,
    name: str,
    score: float,
    feedback: str,
    app_script_url: str,
    assignment: str = "MLDL-2",
    email: str = "",
    *,
    api_key: str = "",
    target: str = "score",
    timeout: int = 15,
) -> str:
    """
    Google Apps Script Web App으로 채점 결과를 전송한다.

    파라미터
    ----------
    student_id : 학번(문자열)
    name       : 학생 이름
    score      : 점수(정수/실수)
    feedback   : 피드백(문자열)
    app_script_url : Apps Script Web App 배포 URL (/exec)
    assignment : 과제 코드(선택)
    email      : 로그인 이메일(보조 식별; ActiveUser 비활성 환경 대비)
    api_key    : (선택) 서버에서 body.api_key 검증 시 사용
    target     : (선택) 서버 라우팅용 키(예: "score", "feedback")
    timeout    : 요청 타임아웃(초)

    반환
    ----
    사용자 노트북에 바로 출력 가능한 한국어 상태 메시지 문자열
    """

    # 전송 페이로드
    payload: Dict[str, Any] = {
        "student_id": student_id,
        "name": name,
        "score": score,
        "feedback": feedback,
        "assignment": assignment,
        "target": target,  # 서버에서 라우팅을 쓸 수 있도록 기본 포함(미사용이면 무시됨)
    }
    if email:
        payload["email"] = email
    if api_key:
        payload["api_key"] = api_key

    try:
        r = requests.post(
            app_script_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        # HTTP 레벨 에러(4xx/5xx) → 예외
        r.raise_for_status()

        # JSON 파싱
        try:
            res = r.json()
        except ValueError:
            # JSON이 아니더라도 서버 본문을 함께 보여 주어 진단 가능하게 처리
            body_preview = (r.text or "").strip()
            if len(body_preview) > 300:
                body_preview = body_preview[:300] + "...(truncated)"
            return f"[전송실패] 응답이 JSON 형식이 아닙니다: {body_preview}"

        status, reason = _normalize_response(res)

        if status == "success":
            return f"[저장완료] {assignment} / {student_id}"

        if status == "already_submitted":
            return "[재제출차단] 이미 제출된 기록이 있어 저장되지 않았습니다."

        # 그 밖의 에러: 서버 메시지 함께 노출
        msg = res.get("message") or res.get("detail") or res.get("error") or res
        return f"[전송실패] {msg}"

    except requests.exceptions.Timeout:
        return "[전송실패] 네트워크 지연으로 시간 초과되었습니다.(timeout)"
    except requests.exceptions.HTTPError as e:
        # 서버 본문 일부를 덧붙여 진단 용이
        body_preview = ""
        try:
            body_preview = r.text.strip()
            if len(body_preview) > 300:
                body_preview = body_preview[:300] + "...(truncated)"
        except Exception:
            pass
        return f"[전송실패] HTTP 오류: {e}; 응답 본문: {body_preview}"
    except requests.exceptions.RequestException as e:
        return f"[전송실패] 네트워크/요청 오류: {e}"
    except Exception as e:
        return f"[전송실패] 처리 중 예외: {e}"
