# gradinglib/submit.py
import json
from typing import Any, Dict, Tuple, Optional
import requests
import hmac, hashlib, base64
from urllib.parse import urlencode
import collections 

# 코랩 버튼 렌더링용
def _display_html(html: str):
    try:
        from IPython.display import HTML, display  # Colab/Jupyter에서만
        display(HTML(html))
    except Exception:
        pass

# [삭제됨] 서명 함수

# --- [핵심 수정] 학번/이름 확인 로직 복원 ---
def show_submit_button(
    webapp_url: str,
    secret: bytes | str, # (secret 파라미터는 받지만 사용하지 않음)
    *,
    student_id: str,
    name: str,
    exam_code: str,
    score: float,          
    feedback: str = "",
    title: str = "채점 완료",
) -> str:
    """
    [수정됨] 
    서버(Apps Script)로 직접 POST 요청을 전송합니다.
    """
    
    # 1. 전송할 페이로드
    payload_data = {
        "student_id": str(student_id).strip(),
        "name": str(name).strip(),
        "exam_code": exam_code,
        "score": score,
        "feedback": feedback,
    }

    # 2. [복원됨] 학번/이름 미입력 방지
    html_result = ""
    debug_message = ""
    
    if not student_id or student_id.lower() == "none" or not name or name.lower() == "none":
        html_result = f"""
        <div style="font-family:system-ui; padding:12px; border:1px solid #b00020; background: #fce8e6; border-radius:12px;">
            <h3 style="margin:0 0 8px 0; color: #b00020;">❌ 제출 실패</h3>
            <p style="color:#b00020; margin-top:8px;"><b>오류: Colab 상단의 '학번과 이름을 입력하고 실행하세요' 셀을 먼저 실행해야 합니다.</b></p>
        </div>
        """
        debug_message = "[Failed] Reason: No student_id or name"
        _display_html(html_result)
        return debug_message

    # 3. Apps Script로 직접 POST 요청 전송
    try:
        r = requests.post(
            webapp_url,
            json=payload_data,
            headers={"Content-Type": "application/json"},
            timeout=20, 
        )
        r.raise_for_status() 
        
        # 4. Code.gs로부터 받은 JSON 응답 파싱
        res = r.json()
        message = res.get("message", "알 수 없는 응답입니다.")

        if res.get("ok") is True:
            # [성공]
            html_result = f"""
            <div style="font-family:system-ui; padding:12px; border:1px solid #137333; background: #e6f4ea; border-radius:12px;">
                <h3 style="margin:0 0 8px 0; color: #137333;">✅ 제출 완료</h3>
                <div><b>시험코드:</b> {exam_code}</div>
                <div><b>학번/이름:</b> {student_id} / {name}</div>
                <div><b>점수:</b> {score}</div>
                <p style="color:#137333; margin-top:8px;"><b>{message}</b></p>
            </div>
            """
            debug_message = f"[Success] {message}"
        else:
            # [실패] (중복 제출, 로그인 오류 등)
            reason = res.get("reason", "unknown_error")
            html_result = f"""
            <div style="font-family:system-ui; padding:12px; border:1px solid #b00020; background: #fce8e6; border-radius:12px;">
                <h3 style="margin:0 0 8px 0; color: #b00020;">❌ 제출 실패</h3>
                <div><b>시험코드:</b> {exam_code}</div>
                <p style="color:#b00020; margin-top:8px;"><b>오류: {message}</b> (코드: {reason})</p>
            </div>
            """
            debug_message = f"[Failed] Reason: {reason}, Message: {message}"

    except requests.exceptions.HTTPError as e:
        html_result = f"<h3>❌ HTTP 오류</h3><p>서버가 오류를 반환했습니다: {e}. (응답: {e.response.text})</p>"
        debug_message = f"[Debug] HTTP error: {e}"
    except requests.exceptions.Timeout:
        html_result = "<h3>❌ 시간 초과</h3><p>서버에 연결하는 데 시간이 너무 오래 걸립니다.</p>"
        debug_message = "[Debug] Request Timeout"
    except requests.exceptions.RequestException as e:
        html_result = "<h3>❌ 네트워크 오류</h3><p>서버에 연결할 수 없습니다: {e}</p>"
        debug_message = f"[Debug] Network error: {e}"
    except Exception as e:
        html_result = f"<h3>❌ 알 수 없는 오류</h3><p>제출 중 예기치 않은 오류가 발생했습니다: {e}</p>"
        debug_message = f"[Debug] Unknown error: {e}"

    # 5. Colab에 결과 HTML 표시
    _display_html(html_result)
    
    # 6. __init__.py로 디버그 메시지 반환 (Colab 셀에 출력됨)
    return debug_message


# ---------------- 기존 서버→서버 POST (필요 시 유지) ----------------
# (이하 `_normalize_response` 및 `save_result_via_appsscript` 함수는
#  수정 없이 그대로 둡니다.)
# ------------------------------------------------------------------

def _normalize_response(res: Dict[str, Any]) -> Tuple[str, str]:
    if "ok" in res:
        if res.get("ok") is True:
            return "success", ""
        reason = str(res.get("reason", "")).strip().lower()
        if reason == "already_submitted":
            return "already_submitted", reason or "already_submitted"
        return "error", reason
    if "status" in res:
        status = str(res.get("status", "")).strip().lower()
        reason = str(res.get("reason") or "").strip().lower()
        if status == "success":
            return "success", ""
        if reason == "already_submitted":
            return "already_submitted", reason
        if status == "error":
            return "error", reason
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
    payload: Dict[str, Any] = {
        "student_id": student_id,
        "name": name,
        "score": score,
        "feedback": feedback,
        "assignment": assignment,
        "target": target,
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
        r.raise_for_status()
        try:
            res = r.json()
        except ValueError:
            body_preview = (r.text or "").strip()
            if len(body_preview) > 300:
                body_preview = body_body_preview[:300] + "...(truncated)"
            return f"[전송실패] 응답이 JSON 형식이 아닙니다: {body_preview}"
        status, reason = _normalize_response(res)
        if status == "success":
            return f"[저장완료] {assignment} / {student_id}"
        if status == "already_submitted":
            return "[재제출차단] 이미 제출된 기록이 있어 저장되지 않았습니다."
        msg = res.get("message") or res.get("detail") or res.get("error") or res
        return f"[전송실패] {msg}"
    except requests.exceptions.Timeout:
        return "[전송실패] 네트워크 지연으로 시간 초과되었습니다.(timeout)"
    except requests.exceptions.HTTPError as e:
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
